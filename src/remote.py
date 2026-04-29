"""
Media-player entity functions.

:copyright: (c) 2026 by Albaintor inc
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any

from ucapi import EntityTypes, Remote, StatusCodes
from ucapi.remote import Attributes, Commands, Features, Options
from ucapi.remote import States as RemoteStates

from client import PanasonicBlurayDevice
from config import DeviceInstance, create_entity_id
from const import (
    KEYS,
    PANASONIC_REMOTE_BUTTONS_MAPPING,
    PANASONIC_REMOTE_UI_PAGES,
    PANASONIC_SIMPLE_COMMANDS,
    States,
)

_LOG = logging.getLogger(__name__)

PANASONIC_REMOTE_STATE_MAPPING = {
    States.UNKNOWN: RemoteStates.UNKNOWN,
    States.UNAVAILABLE: RemoteStates.UNAVAILABLE,
    States.OFF: RemoteStates.OFF,
    States.ON: RemoteStates.ON,
    States.PLAYING: RemoteStates.ON,
    States.PAUSED: RemoteStates.ON,
    States.STOPPED: RemoteStates.ON,
}


class PanasonicRemote(Remote):
    """Representation of a Kodi Media Player entity."""

    def __init__(self, config_device: DeviceInstance, device: PanasonicBlurayDevice):
        """Initialize the class."""
        self._device = device
        _LOG.debug("PanasonicRemote init")
        entity_id = create_entity_id(config_device.id, EntityTypes.REMOTE)
        features = [Features.SEND_CMD, Features.ON_OFF, Features.TOGGLE]
        attributes = {
            Attributes.STATE: PANASONIC_REMOTE_STATE_MAPPING.get(device.state),
        }
        super().__init__(
            identifier=entity_id,
            name=config_device.name,
            features=features,
            attributes=attributes,
            simple_commands=list(PANASONIC_SIMPLE_COMMANDS.keys()),
            button_mapping=PANASONIC_REMOTE_BUTTONS_MAPPING,
            ui_pages=PANASONIC_REMOTE_UI_PAGES,
        )

    def get_int_param(self, param: str, params: dict[str, Any], default: int):
        """Extract int parameters."""
        # TODO bug to be fixed on UC Core : some params are sent as (empty) strings by remote (hold == "")
        value = params.get(param, default)
        if isinstance(value, str) and len(value) > 0:
            return int(float(value))
        return default

    async def command(self, cmd_id: str, params: dict[str, Any] | None = None, *, websocket: Any) -> StatusCodes:
        """
        Media-player entity command handler.

        Called by the integration-API if a command is sent to a configured media-player entity.

        :param cmd_id: command
        :param params: optional command parameters
        :return: status code of the command request
        """
        _LOG.info("Got %s command request: %s %s", self.id, cmd_id, params)

        if self._device is None:
            _LOG.warning("No Kodi instance for entity: %s", self.id)
            return StatusCodes.SERVICE_UNAVAILABLE

        repeat = self.get_int_param("repeat", params, 1)
        res = StatusCodes.OK
        for _ in range(0, repeat):
            res = await self.handle_command(cmd_id, params)
        return res

    async def handle_command(self, cmd_id: str, params: dict[str, Any] | None = None) -> StatusCodes:
        """Handle remote command."""
        # pylint: disable=R0911
        # hold = self.getIntParam("hold", params, 0)
        delay = self.get_int_param("delay", params, 0)
        command = params.get("command", "")

        if command in KEYS:
            return await self._device.send_key(command)
        if command in self.options[Options.SIMPLE_COMMANDS]:
            return await self._device.send_key(PANASONIC_SIMPLE_COMMANDS[command])
        if cmd_id == Commands.ON:
            return await self._device.turn_on()
        if cmd_id == Commands.OFF:
            return await self._device.turn_off()
        if cmd_id == Commands.TOGGLE:
            return await self._device.toggle()
        if cmd_id == Commands.SEND_CMD:
            return await self._device.send_key(command)
        if cmd_id == Commands.SEND_CMD_SEQUENCE:
            commands = params.get("sequence", [])  # .split(",")
            res = StatusCodes.OK
            for command in commands:
                res = await self.handle_command(Commands.SEND_CMD, {"command": command, "params": params})
                if delay > 0:
                    await asyncio.sleep(delay)
        else:
            return StatusCodes.NOT_IMPLEMENTED
        if delay > 0 and cmd_id != Commands.SEND_CMD_SEQUENCE:
            await asyncio.sleep(delay)
        return res

    def _key_update_helper(self, key: str, value: str | None, attributes):
        if value is None:
            return attributes

        if key in self.attributes:
            if self.attributes[key] != value:
                attributes[key] = value
        else:
            attributes[key] = value

        return attributes

    # pylint: disable=R0801
    def filter_changed_attributes(self, update: dict[str, Any]) -> dict[str, Any]:
        """
        Filter the given attributes and return only the changed values.

        :param update: dictionary with attributes.
        :return: filtered entity attributes containing changed attributes only.
        """
        attributes = {}

        if Attributes.STATE in update:
            state = PANASONIC_REMOTE_STATE_MAPPING.get(update[Attributes.STATE])
            attributes = self._key_update_helper(Attributes.STATE, state, attributes)

        _LOG.debug("PanasonicRemote update attributes %s -> %s", update, attributes)
        return attributes
