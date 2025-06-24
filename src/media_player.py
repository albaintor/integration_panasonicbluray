"""
Media-player entity functions.

:copyright: (c) 2023 by Unfolded Circle ApS.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import logging
from typing import Any

import client
from client import PanasonicBlurayDevice
from config import DeviceInstance, create_entity_id
from ucapi import EntityTypes, MediaPlayer, StatusCodes
from ucapi.media_player import Attributes, Commands, DeviceClasses, Features, States, MediaType, Options

from const import MEDIA_PLAYER_STATE_MAPPING, PANASONIC_SIMPLE_COMMANDS

_LOG = logging.getLogger(__name__)


class PanasonicMediaPlayer(MediaPlayer):
    """Representation of a Sony Media Player entity."""

    def __init__(self, config_device: DeviceInstance, device: PanasonicBlurayDevice):
        """Initialize the class."""
        self._device = device

        entity_id = create_entity_id(config_device.id, EntityTypes.MEDIA_PLAYER)
        features = [
            Features.ON_OFF,
            Features.TOGGLE,
            Features.MEDIA_TYPE,
            Features.PLAY_PAUSE,
            Features.DPAD,
            Features.SETTINGS,
            Features.STOP,
            Features.EJECT,
            Features.FAST_FORWARD,
            Features.REWIND,
            Features.MENU,
            Features.CONTEXT_MENU,
            Features.NUMPAD,
            Features.CHANNEL_SWITCHER,
            Features.MEDIA_POSITION,
            Features.MEDIA_DURATION,
            Features.INFO,
            Features.AUDIO_TRACK,
            Features.SUBTITLE,
            Features.COLOR_BUTTONS,
            Features.HOME,
            Features.PREVIOUS,
            Features.NEXT
        ]
        attributes = {
            Attributes.STATE: state_from_device(device.state),
            Attributes.MEDIA_POSITION: device.media_position,
            Attributes.MEDIA_DURATION: device.media_duration,
            Attributes.MEDIA_TYPE: MediaType.VIDEO,
        }

        options = {
            Options.SIMPLE_COMMANDS: list(PANASONIC_SIMPLE_COMMANDS.keys())
        }
        super().__init__(
            entity_id,
            config_device.name,
            features,
            attributes,
            device_class=DeviceClasses.STREAMING_BOX,
            options=options
        )

    async def command(self, cmd_id: str, params: dict[str, Any] | None = None) -> StatusCodes:
        """
        Media-player entity command handler.

        Called by the integration-API if a command is sent to a configured media-player entity.

        :param cmd_id: command
        :param params: optional command parameters
        :return: status code of the command request
        """
        _LOG.info("Got %s command request: %s %s", self.id, cmd_id, params)

        if self._device is None:
            _LOG.warning("No device instance for entity: %s", self.id)
            return StatusCodes.SERVICE_UNAVAILABLE
        elif cmd_id == Commands.ON:
            return await self._device.turn_on()
        elif cmd_id == Commands.OFF:
            return await self._device.turn_off()
        elif cmd_id == Commands.TOGGLE:
            return await self._device.toggle()
        elif cmd_id == Commands.CHANNEL_UP:
            return await self._device.channel_up()
        elif cmd_id == Commands.CHANNEL_DOWN:
            return await self._device.channel_down()
        elif cmd_id == Commands.PLAY_PAUSE:
            return await self._device.play_pause()
        elif cmd_id == Commands.STOP:
            return await self._device.stop()
        elif cmd_id == Commands.EJECT:
            return await self._device.eject()
        elif cmd_id == Commands.FAST_FORWARD:
            return await self._device.fast_forward()
        elif cmd_id == Commands.REWIND:
            return await self._device.rewind()
        elif cmd_id == Commands.CURSOR_UP:
            return await self._device.send_key("UP")
        elif cmd_id == Commands.CURSOR_DOWN:
            return await self._device.send_key("DOWN")
        elif cmd_id == Commands.CURSOR_LEFT:
            return await self._device.send_key("LEFT")
        elif cmd_id == Commands.CURSOR_RIGHT:
            return await self._device.send_key("RIGHT")
        elif cmd_id == Commands.CURSOR_ENTER:
            return await self._device.send_key("SELECT")
        elif cmd_id == Commands.BACK:
            return await self._device.send_key("RETURN")
        elif cmd_id == Commands.MENU:
            return await self._device.send_key("MENU")
        elif cmd_id == Commands.CONTEXT_MENU:
            return await self._device.send_key("PUPMENU")
        elif cmd_id == Commands.SETTINGS:
            return await self._device.send_key("SETUP")
        elif cmd_id == Commands.HOME:
            return await self._device.send_key("TITLE")
        elif cmd_id == Commands.AUDIO_TRACK:
            return await self._device.send_key("AUDIOSEL")
        elif cmd_id == Commands.SUBTITLE:
            return await self._device.send_key("TITLEONOFF")  # CLOSED_CAPTION?
        elif cmd_id == Commands.DIGIT_0:
            return await self._device.send_key("D0")
        elif cmd_id == Commands.DIGIT_1:
            return await self._device.send_key("D1")
        elif cmd_id == Commands.DIGIT_2:
            return await self._device.send_key("D2")
        elif cmd_id == Commands.DIGIT_3:
            return await self._device.send_key("D3")
        elif cmd_id == Commands.DIGIT_4:
            return await self._device.send_key("D4")
        elif cmd_id == Commands.DIGIT_5:
            return await self._device.send_key("D5")
        elif cmd_id == Commands.DIGIT_6:
            return await self._device.send_key("D6")
        elif cmd_id == Commands.DIGIT_7:
            return await self._device.send_key("D7")
        elif cmd_id == Commands.DIGIT_8:
            return await self._device.send_key("D8")
        elif cmd_id == Commands.DIGIT_9:
            return await self._device.send_key("D9")
        elif cmd_id == Commands.INFO:
            return await self._device.send_key("PLAYBACKINFO")
        elif cmd_id == Commands.FUNCTION_RED:
            return await self._device.send_key("RED")
        elif cmd_id == Commands.FUNCTION_BLUE:
            return await self._device.send_key("BLUE")
        elif cmd_id == Commands.FUNCTION_YELLOW:
            return await self._device.send_key("YELLOW")
        elif cmd_id == Commands.FUNCTION_GREEN:
            return await self._device.send_key("GREEN")
        elif cmd_id == Commands.NEXT:
            return await self._device.send_key("MNSKIP")
        elif cmd_id == Commands.PREVIOUS:
            return await self._device.send_key("MNBACK")
        elif cmd_id in self.options[Options.SIMPLE_COMMANDS]:
            return await self._device.send_key(PANASONIC_SIMPLE_COMMANDS[cmd_id])
        else:
            return StatusCodes.NOT_IMPLEMENTED

    def filter_changed_attributes(self, update: dict[str, Any]) -> dict[str, Any]:
        """
        Filter the given attributes and return only the changed values.

        :param update: dictionary with attributes.
        :return: filtered entity attributes containing changed attributes only.
        """
        attributes = {}

        if Attributes.STATE in update:
            state = update[Attributes.STATE]
            attributes = self._key_update_helper(Attributes.STATE, state, attributes)

        for attr in [
            Attributes.MEDIA_POSITION,
            Attributes.MEDIA_DURATION,
            Attributes.MEDIA_TYPE,
        ]:
            if attr in update:
                attributes = self._key_update_helper(attr, update[attr], attributes)

        _LOG.debug("MediaPlayer update attributes %s -> %s", update, attributes)
        return attributes

    def _key_update_helper(self, key: str, value: str | None, attributes):
        if value is None:
            return attributes

        if key in self.attributes:
            if self.attributes[key] != value:
                attributes[key] = value
        else:
            attributes[key] = value

        return attributes


def state_from_device(client_state: client.States) -> States:
    """
    Convert Device state to UC API media-player state.

    :param client_state: Orange STB  state
    :return: UC API media_player state
    """
    if client_state in MEDIA_PLAYER_STATE_MAPPING:
        return MEDIA_PLAYER_STATE_MAPPING[client_state]
    return States.UNKNOWN
