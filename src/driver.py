#!/usr/bin/env python3
"""
This module implements a Remote Two integration driver for Orange STB.

:copyright: (c) 2023 by Unfolded Circle ApS.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import asyncio
import json
import logging
import os
from typing import Any

import ucapi
import ucapi.api_definitions as uc
import websockets
from ucapi.api import filter_log_msg_data, IntegrationAPI
from ucapi.media_player import Attributes as MediaAttr, MediaType

import client
import config
import media_player
import remote
import setup_flow
from client import PanasonicBlurayDevice
from config import device_from_entity_id

_LOG = logging.getLogger("driver")  # avoid having __main__ in log messages
_LOOP = asyncio.get_event_loop()

# Global variables
api = ucapi.IntegrationAPI(_LOOP)
# Map of device_id -> Orange instance
_configured_devices: dict[str, PanasonicBlurayDevice] = {}
_R2_IN_STANDBY = False


@api.listens_to(ucapi.Events.CONNECT)
async def on_r2_connect_cmd() -> None:
    """Connect all configured receivers when the Remote Two sends the connect command."""
    # TODO check if we were in standby and ignore the call? We'll also get an EXIT_STANDBY
    _LOG.debug("R2 connect command: connecting device(s)")
    await api.set_device_state(ucapi.DeviceStates.CONNECTED)
    for device in _configured_devices.values():
        # start background task
        await device.connect()
        await _LOOP.create_task(device.update())


@api.listens_to(ucapi.Events.DISCONNECT)
async def on_r2_disconnect_cmd():
    """Disconnect all configured receivers when the Remote Two sends the disconnect command."""
    for device in _configured_devices.values():
        # start background task
        await device.disconnect()


@api.listens_to(ucapi.Events.ENTER_STANDBY)
async def on_r2_enter_standby() -> None:
    """
    Enter standby notification from Remote Two.
    Disconnect every OrangeTV instances.
    """
    global _R2_IN_STANDBY
    _R2_IN_STANDBY = True
    _LOG.debug("Enter standby event: disconnecting device(s)")
    for device in _configured_devices.values():
        # start background task
        await device.disconnect()


@api.listens_to(ucapi.Events.EXIT_STANDBY)
async def on_r2_exit_standby() -> None:
    """
    Exit standby notification from Remote Two.

    Connect all OrangeTV instances.
    """
    global _R2_IN_STANDBY

    _R2_IN_STANDBY = False
    _LOG.debug("Exit standby event: connecting device(s)")

    for device in _configured_devices.values():
        # start background task
        await device.connect()
        await _LOOP.create_task(device.update())


@api.listens_to(ucapi.Events.SUBSCRIBE_ENTITIES)
async def on_subscribe_entities(entity_ids: list[str]) -> None:
    """
    Subscribe to given entities.

    :param entity_ids: entity identifiers.
    """
    global _R2_IN_STANDBY

    _R2_IN_STANDBY = False
    _LOG.debug("Subscribe entities event: %s", entity_ids)
    for entity_id in entity_ids:
        entity = api.configured_entities.get(entity_id)
        device_id = device_from_entity_id(entity_id)
        if device_id in _configured_devices:
            device = _configured_devices[device_id]
            if isinstance(entity, media_player.PanasonicMediaPlayer):
                api.configured_entities.update_attributes(entity_id,
          {ucapi.media_player.Attributes.STATE: media_player.state_from_device(device.state)})
            if isinstance(entity, remote.PanasonicRemote):
                api.configured_entities.update_attributes(entity_id,
          {ucapi.remote.Attributes.STATE: remote.PANASONIC_REMOTE_STATE_MAPPING.get(device.state)})
            continue

        device = config.devices.get(device_id)
        if device:
            _configure_new_device(device, connect=True)
        else:
            _LOG.error("Failed to subscribe entity %s: no device configuration found", entity_id)


@api.listens_to(ucapi.Events.UNSUBSCRIBE_ENTITIES)
async def on_unsubscribe_entities(entity_ids: list[str]) -> None:
    """On unsubscribe, we disconnect the objects and remove listeners for events."""
    _LOG.debug("Unsubscribe entities event: %s", entity_ids)
    devices_to_remove = set()
    for entity_id in entity_ids:
        device_id = device_from_entity_id(entity_id)
        if device_id is None:
            continue
        devices_to_remove.add(device_id)

    # Keep devices that are used by other configured entities not in this list
    for entity in api.configured_entities.get_all():
        entity_id = entity.get("entity_id")
        if entity_id in entity_ids:
            continue
        device_id = device_from_entity_id(entity_id)
        if device_id is None:
            continue
        if device_id in devices_to_remove:
            devices_to_remove.remove(device_id)

    for device_id in devices_to_remove:
        if device_id in _configured_devices:
            await _configured_devices[device_id].disconnect()
            _configured_devices[device_id].events.remove_all_listeners()


async def on_device_connected(device_id: str):
    """Handle AVR connection."""
    _LOG.debug("Device connected: %s", device_id)
    await api.set_device_state(ucapi.DeviceStates.CONNECTED)
    if device_id not in _configured_devices:
        _LOG.warning("Device %s is not configured", device_id)
        return

    # TODO #20 when multiple devices are supported, the device state logic isn't that simple anymore!
    await api.set_device_state(ucapi.DeviceStates.CONNECTED)

    for entity_id in _entities_from_device(device_id):
        configured_entity = api.configured_entities.get(entity_id)
        if configured_entity is None:
            continue

        if configured_entity.entity_type == ucapi.EntityTypes.MEDIA_PLAYER:
            if (configured_entity.attributes[ucapi.media_player.Attributes.STATE]
                    == ucapi.media_player.States.UNAVAILABLE):
                api.configured_entities.update_attributes(
                    entity_id, {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.STANDBY}
                )
        elif configured_entity.entity_type == ucapi.EntityTypes.REMOTE:
            if (configured_entity.attributes[ucapi.remote.Attributes.STATE]
                    == ucapi.remote.States.UNAVAILABLE):
                api.configured_entities.update_attributes(
                    entity_id, {ucapi.remote.Attributes.STATE: ucapi.remote.States.OFF}
                )


async def on_device_disconnected(avr_id: str):
    """Handle AVR disconnection."""
    _LOG.debug("AVR disconnected: %s", avr_id)

    for entity_id in _entities_from_device(avr_id):
        configured_entity = api.configured_entities.get(entity_id)
        if configured_entity is None:
            continue

        if configured_entity.entity_type == ucapi.EntityTypes.MEDIA_PLAYER:
            api.configured_entities.update_attributes(
                entity_id, {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.UNAVAILABLE}
            )
        elif configured_entity.entity_type == ucapi.EntityTypes.REMOTE:
            api.configured_entities.update_attributes(
                entity_id, {ucapi.remote.Attributes.STATE: ucapi.remote.States.UNAVAILABLE}
            )

    # TODO #20 when multiple devices are supported, the device state logic isn't that simple anymore!
    await api.set_device_state(ucapi.DeviceStates.DISCONNECTED)


async def on_avr_connection_error(avr_id: str, message):
    """Set entities of AVR to state UNAVAILABLE if AVR connection error occurred."""
    _LOG.error(message)

    for entity_id in _entities_from_device(avr_id):
        configured_entity = api.configured_entities.get(entity_id)
        if configured_entity is None:
            continue

        if configured_entity.entity_type == ucapi.EntityTypes.MEDIA_PLAYER:
            api.configured_entities.update_attributes(
                entity_id, {ucapi.media_player.Attributes.STATE: ucapi.media_player.States.UNAVAILABLE}
            )
        elif configured_entity.entity_type == ucapi.EntityTypes.REMOTE:
            api.configured_entities.update_attributes(
                entity_id, {ucapi.remote.Attributes.STATE: ucapi.remote.States.UNAVAILABLE}
            )

    # TODO #20 when multiple devices are supported, the device state logic isn't that simple anymore!
    await api.set_device_state(ucapi.DeviceStates.ERROR)


async def handle_avr_address_change(avr_id: str, address: str) -> None:
    """Update device configuration with changed IP address."""
    device = config.devices.get(avr_id)
    if device and device.address != address:
        _LOG.info("Updating IP address of configured AVR %s: %s -> %s", avr_id, device.address, address)
        device.address = address
        config.devices.update(device)


async def on_avr_update(device_id: str, update: dict[str, Any] | None) -> None:
    """
    Update attributes of configured media-player entity if device properties changed.

    :param device_id: AVR identifier
    :param update: dictionary containing the updated properties or None if
    """
    if update is None:
        if device_id not in _configured_devices:
            return
        device = _configured_devices[device_id]
        update = {
            MediaAttr.STATE: device.state,
            MediaAttr.MEDIA_POSITION: device.media_position,
            MediaAttr.MEDIA_DURATION: device.media_duration,
            MediaAttr.MEDIA_TYPE: MediaType.VIDEO,
        }
    else:
        _LOG.info("[%s] Panasonic update: %s", device_id, update)

    attributes = None

    # TODO awkward logic: this needs better support from the integration library
    for entity_id in _entities_from_device(device_id):
        configured_entity = api.configured_entities.get(entity_id)
        if configured_entity is None:
            return

        if isinstance(configured_entity, media_player.PanasonicMediaPlayer):
            attributes = configured_entity.filter_changed_attributes(update)
        elif isinstance(configured_entity, remote.PanasonicRemote):
            attributes = configured_entity.filter_changed_attributes(update)

        if attributes:
            api.configured_entities.update_attributes(entity_id, attributes)


def _entities_from_device(device_id: str) -> list[str]:
    """
    Return all associated entity identifiers of the given AVR.

    :param device_id: the AVR identifier
    :return: list of entity identifiers
    """
    # dead simple for now: one media_player entity per device!
    # TODO #21 support multiple zones: one media-player per zone
    return [f"media_player.{device_id}", f"remote.{device_id}"]


def _configure_new_device(device_config: config.DeviceInstance, connect: bool = True) -> None:
    """
    Create and configure a new device.

    Supported entities of the device are created and registered in the integration library as available entities.

    :param device_config: the device configuration.
    :param connect: True: start connection to receiver.
    """
    # the device should not yet be configured, but better be safe
    if device_config.id in _configured_devices:
        device = _configured_devices[device_config.id]
    else:
        device = PanasonicBlurayDevice(device_config)

        device.events.on(client.Events.CONNECTED, on_device_connected)
        device.events.on(client.Events.ERROR, on_avr_connection_error)
        device.events.on(client.Events.UPDATE, on_avr_update)
        # receiver.events.on(avr.Events.IP_ADDRESS_CHANGED, handle_avr_address_change)
        _configured_devices[device_config.id] = device

    if connect:
        # start background connection task
        _LOOP.create_task(device.update())
        _LOOP.create_task(on_device_connected(device_config.id))
    _register_available_entities(device_config, device)


def _register_available_entities(config_device: config.DeviceInstance, device: PanasonicBlurayDevice) -> None:
    """
    Create entities for given receiver device and register them as available entities.

    :param config_device: device
    """
    # plain and simple for now: only one media_player per AVR device
    # entity = media_player.create_entity(device)
    entities = [media_player.PanasonicMediaPlayer(config_device, device),
                remote.PanasonicRemote(config_device, device)]
    for entity in entities:
        if api.available_entities.contains(entity.id):
            api.available_entities.remove(entity.id)
        api.available_entities.add(entity)


def on_device_added(device: config.DeviceInstance) -> None:
    """Handle a newly added device in the configuration."""
    _LOG.debug("New device added: %s", device)
    _configure_new_device(device, connect=False)


def on_device_updated(device: config.DeviceInstance) -> None:
    """Handle an updated device in the configuration."""
    _LOG.debug("Device config updated: %s, reconnect with new configuration", device)
    _configure_new_device(device, connect=True)


def on_device_removed(device: config.DeviceInstance | None) -> None:
    """Handle a removed device in the configuration."""
    if device is None:
        _LOG.debug("Configuration cleared, disconnecting & removing all configured AVR instances")
        for configured in _configured_devices.values():
            _LOOP.create_task(_async_remove(configured))
        _configured_devices.clear()
        api.configured_entities.clear()
        api.available_entities.clear()
    else:
        if device.id in _configured_devices:
            _LOG.debug("Disconnecting from removed AVR %s", device.id)
            configured = _configured_devices.pop(device.id)
            _LOOP.create_task(_async_remove(configured))
            for entity_id in _entities_from_device(configured.id):
                api.configured_entities.remove(entity_id)
                api.available_entities.remove(entity_id)


async def _async_remove(device: PanasonicBlurayDevice) -> None:
    """Disconnect from receiver and remove all listeners."""
    # await device.disconnect()
    device.events.remove_all_listeners()


async def main():
    """Start the Remote Two integration driver."""
    logging.basicConfig()

    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()
    logging.getLogger("client").setLevel(level)
    logging.getLogger("discover").setLevel(level)
    logging.getLogger("driver").setLevel(level)
    logging.getLogger("media_player").setLevel(level)
    logging.getLogger("receiver").setLevel(level)
    logging.getLogger("setup_flow").setLevel(level)
    logging.getLogger("remote").setLevel(level)

    config.devices = config.Devices(api.config_dir_path, on_device_added, on_device_removed, on_device_updated)
    for device in config.devices.all():
        _LOG.debug("UC Orange device %s %s", device.id, device.address)
        _configure_new_device(device, connect=False)

    # _LOOP.create_task(receiver_status_poller())
    for device in _configured_devices.values():
        if not device.is_on:
            continue
        _LOOP.create_task(device.update())

    await api.init("driver.json", setup_flow.driver_setup_handler)


if __name__ == "__main__":
    _LOOP.run_until_complete(main())
    _LOOP.run_forever()
