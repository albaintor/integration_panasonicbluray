#!/usr/bin/env python
# coding: utf-8
import asyncio
from functools import wraps
from typing import Callable, Concatenate, Awaitable, Any, Coroutine, TypeVar, ParamSpec

import aiohttp
from asyncio import Lock, CancelledError
import logging
from enum import IntEnum


import ucapi.media_player
from aiohttp import ClientSession, ClientError
from config import DeviceInstance
from pyee import AsyncIOEventEmitter
from ucapi.media_player import Attributes

from const import States, USER_AGENT, KEYS, PlayerVariant, MEDIA_PLAYER_STATE_MAPPING

_LOGGER = logging.getLogger(__name__)


class Events(IntEnum):
    """Internal driver events."""

    CONNECTED = 0
    ERROR = 1
    UPDATE = 2
    IP_ADDRESS_CHANGED = 3
    DISCONNECTED = 4


_PanasonicDeviceT = TypeVar("_PanasonicDeviceT", bound="PanasonicDevice")
_P = ParamSpec("_P")

CONNECTION_RETRIES=10


def cmd_wrapper(
        func: Callable[Concatenate[_PanasonicDeviceT, _P], Awaitable[ucapi.StatusCodes | list]],
) -> Callable[Concatenate[_PanasonicDeviceT, _P], Coroutine[Any, Any, ucapi.StatusCodes | list]]:
    """Catch command exceptions."""

    @wraps(func)
    async def wrapper(obj: _PanasonicDeviceT, *args: _P.args, **kwargs: _P.kwargs) -> ucapi.StatusCodes:
        """Wrap all command methods."""
        try:
            res = await func(obj, *args, **kwargs)
            await obj.start_polling()
            if res[0] == 'error':
                return ucapi.StatusCodes.BAD_REQUEST
            return ucapi.StatusCodes.OK
        except ClientError as exc:
            # If Kodi is off, we expect calls to fail.
            if obj.state == States.OFF:
                log_function = _LOGGER.debug
            else:
                log_function = _LOGGER.error
            log_function(
                "Error calling %s on entity %s: %r trying to reconnect and send the command next",
                func.__name__,
                obj.id,
                exc,
            )
            # Kodi not connected, launch a connect task but
            # don't wait more than 5 seconds, then process the command if connected
            # else returns error
            connect_task = obj.event_loop.create_task(obj.connect())
            await asyncio.sleep(0)
            try:
                async with asyncio.timeout(5):
                    await connect_task
            except asyncio.TimeoutError:
                log_function(
                    "Timeout for reconnect, command won't be sent"
                )
                pass
            else:
                if not obj._connect_error:
                    try:
                        await func(obj, *args, **kwargs)
                        return ucapi.StatusCodes.OK
                    except ClientError as exc:
                        log_function(
                            "Error calling %s on entity %s: %r trying to reconnect",
                            func.__name__,
                            obj.id,
                            exc,
                        )
            return ucapi.StatusCodes.BAD_REQUEST
        except Exception as ex:
            _LOGGER.error(
                "Unknown error %s",
                func.__name__)

    return wrapper


class PanasonicBlurayDevice(object):
    def __init__(self, device_config: DeviceInstance, timeout=3, refresh_frequency=60):
        from datetime import timedelta
        self._id = device_config.id
        self._name = device_config.name
        self._hostname = device_config.address
        self._device_config = device_config
        self._timeout = timeout
        self.refresh_frequency = timedelta(seconds=refresh_frequency)
        self._state = States.UNKNOWN
        self._event_loop = asyncio.get_event_loop() or asyncio.get_running_loop()
        self.events = AsyncIOEventEmitter(self._event_loop)
        self._update_lock = Lock()
        self._session: ClientSession | None = None
        self._variant = PlayerVariant.AUTO
        self._media_position = 0
        self._media_duration = 0
        self._update_task = None
        self._update_lock = Lock()

    async def connect(self):
        if self._session:
            await self._session.close()
            self._session = None
        session_timeout = aiohttp.ClientTimeout(total=None, sock_connect=self._timeout, sock_read=self._timeout)
        self._session = aiohttp.ClientSession(headers={"User-Agent": USER_AGENT},
                                              timeout=session_timeout,
                                              raise_for_status=True)
        self.events.emit(Events.CONNECTED, self.id)
        await self.start_polling()

    async def disconnect(self):
        if self._session:
            await self._session.close()
            self._session = None

    async def start_polling(self):
        """Start polling task."""
        if self._update_task is not None:
            return
        await self._update_lock.acquire()
        if self._update_task is not None:
            return
        _LOGGER.debug("Start polling task for device %s", self.id)
        self._update_task = self._event_loop.create_task(self._background_update_task())
        self._update_lock.release()

    async def stop_polling(self):
        """Stop polling task."""
        if self._update_task:
            try:
                self._update_task.cancel()
            except CancelledError:
                pass
            self._update_task = None

    async def _background_update_task(self):
        self._reconnect_retry = 0
        while True:
            if not self._device_config.always_on:
                if self.state == States.OFF:
                    self._reconnect_retry += 1
                    if self._reconnect_retry > CONNECTION_RETRIES:
                        _LOGGER.debug("Stopping update task as the device %s is off", self.id)
                        break
                    _LOGGER.debug("Device %s is off, retry %s", self.id, self._reconnect_retry)
                elif self._reconnect_retry > 0:
                    self._reconnect_retry = 0
                    _LOGGER.debug("Device %s is on again", self.id)
            await self.update()
            await asyncio.sleep(10)

        self._update_task = None

    async def update(self):
        if self._update_lock.locked():
            return

        await self._update_lock.acquire()
        # _LOGGER.debug("Refresh Panasonic data")
        if self._session is None:
            await self.connect()
        update_data = {}
        current_state = self.state

        status = await self.get_play_status()

        if status[0] == "error":
            current_state = States.UNAVAILABLE
        elif status[0] in ["off", "standby"]:
            # We map both of these to off. If it's really off we can't
            # turn it on, but from standby we can go to idle by pressing
            # POWER.
            current_state = States.OFF
        elif status[0] == "paused":
            current_state = States.PAUSED
        elif status[0] == "stopped":
            current_state = States.STOPPED
        elif status[0] == "playing":
            current_state = States.PLAYING
        else:
            current_state = States.UNKNOWN

        # Update our current media position + length
        if status[1] >= 0:
            media_position = status[1]
        else:
            media_position = 0

        if status[2] >= 0:
            media_duration = status[2]
        else:
            media_duration = 0

        if current_state != self.state:
            self._state = current_state
            update_data[Attributes.STATE] = MEDIA_PLAYER_STATE_MAPPING.get(self.state,
                                                                           ucapi.media_player.States.UNKNOWN)

        if media_position != self.media_position:
            self._media_position = media_position
            update_data[Attributes.MEDIA_POSITION] = self.media_position
        if media_duration != self.media_duration:
            self._media_duration = media_duration
            update_data[Attributes.MEDIA_DURATION] = self.media_duration

        if update_data:
            self.events.emit(
                Events.UPDATE,
                self.id,
                update_data
            )

        self._update_lock.release()

    async def send_cmd(self, url, data):
        try:
            response = await self._session.post(url, data=data)
        except ClientError:
            # If we can't reach the device, assume it's off
            return ['off', None]

        result = (await response.read()).split(b'\r\n')

        # First line is '00, "", 1' on success.
        # Error response starts with FE, then some binary data
        if result[0].split(b',')[0] != b'00':
            return ['error', None]

        return ['ok', result[1].decode().split(',')]

    async def _send_key(self, key):
        """ Send the supplied keypress to the device """
        # Sanity check it's a valid key
        if key not in KEYS:
            _LOGGER.info("Key not known, let it go anyway %s", key)
            # return ['error', None]

        # Check the player supports it
        if self._variant == PlayerVariant.UB:
            return ['error', None]

        url = 'http://%s/WAN/%s/%s_ctrl.cgi' % (self._hostname, 'dvdr', 'dvdr')
        data = ('cCMD_RC_%s.x=100&cCMD_RC_%s.y=100' % (key, key)).encode()

        resp = await self.send_cmd(url, data)
        # If we're auto-detecting player type then assume we're an newer UB
        # variant if we got an error, and an older BD if it worked
        if self._variant == PlayerVariant.AUTO:
            if resp[0] == 'error':
                self._variant = PlayerVariant.UB
                return ['error', None]
            else:
                self._variant = PlayerVariant.BD
        return resp

    async def get_status(self):
        # Check the player supports it, return a dummy response if not
        if self._variant == PlayerVariant.UB:
            return ['1', '0', '0', '00000000', '0']

        url = 'http://%s/WAN/%s/%s_ctrl.cgi' % (self._hostname, 'dvdr', 'dvdr')
        data = b'cCMD_GET_STATUS.x=100&cCMD_GET_STATUS.y=100'

        resp = await self.send_cmd(url, data)
        if resp[0] == 'error':
            # If we got an error and we're auto-detecting player type assume
            # it's a more modern UB
            if self._variant == PlayerVariant.AUTO:
                self._variant = PlayerVariant.UB
                return ['1', '0', '0', '00000000', '0']
            else:
                return ['error']

        # If we get here and we're still auto-detecting player type we can
        # assume an older BD variant.
        if self._variant == PlayerVariant.AUTO:
            self._variant = PlayerVariant.BD

        if resp[0] == 'off':
            return ['off']

        # Response is of the form:
        #  2,0,0,248,0,1,8,2,0,00000000
        #
        # 0: 0 == standby, playing or paused / 2 == stopped or menu
        # 3: Playing time
        # 4: Total time

        return resp[1]

    async def get_play_status(self):
        url = 'http://%s/WAN/%s/%s_ctrl.cgi' % (self._hostname, 'dvdr', 'dvdr')
        data = b'cCMD_PST.x=100&cCMD_PST.y=100'

        resp = await self.send_cmd(url, data)
        if resp[0] == 'off':
            return ['off', 0, 0]
        elif resp[0] == 'error':
            return ['error', 0, 0]

        # Needed for title length + standby/idle status
        status = await self.get_status()
        if status[0] == 'off':
            return ['off', 0, 0]
        elif status[0] == 'error':
            return ['error', 0, 0]

        # State response is of the form
        #  ['0', '0', '0', '00000000']
        #   0: State (0 == stopped / 1 == playing / 2 == paused)
        #   1: Playing time (-2 for no disc?)
        # 2/3: Unknown

        play_status = resp[1]
        if play_status[0] == '0':
            # Stopped is reported when in standby mode as well, so we have
            # to use the additional status query to work out which state we are
            # in.
            if status[0] == '0':
                state = 'standby'
            else:
                state = 'stopped'
        elif play_status[0] == '1':
            state = 'playing'
        elif play_status[0] == '2':
            state = 'paused'
        else:
            state = 'unknown'

        return [state, int(play_status[1]), int(status[4])]

    @property
    def id(self):
        return self._id

    @property
    def state(self) -> States:
        return self._state

    @property
    def name(self):
        return self._name

    @property
    def media_duration(self):
        return self._media_duration

    @property
    def media_position(self):
        return self._media_position

    @property
    def is_on(self):
        return self.state in [States.PAUSED, States.STOPPED, States.PLAYING, States.ON]

    @cmd_wrapper
    async def send_key(self, key):
        return await self._send_key(key)


    @cmd_wrapper
    async def toggle(self):
        await self._send_key("POWER")

    @cmd_wrapper
    async def turn_on(self):
        if not self.is_on:
            await self._send_key("POWER")

    @cmd_wrapper
    async def turn_off(self):
        if self.is_on:
            await self._send_key("POWER")

    @cmd_wrapper
    async def channel_up(self):
        return await self._send_key("SKIPFWD")

    @cmd_wrapper
    async def channel_down(self):
        return await self._send_key("SKIPREV")

    @cmd_wrapper
    async def play_pause(self):
        if self.state == States.PLAYING:
            return await self._send_key("PAUSE")
        else:
            return await self._send_key("PLAYBACK")

    @cmd_wrapper
    async def play(self):
        return await self._send_key("PLAYBACK")

    @cmd_wrapper
    async def pause(self):
        return await self._send_key("PAUSE")

    @cmd_wrapper
    async def stop(self):
        return await self._send_key("STOP")

    @cmd_wrapper
    async def eject(self):
        return await self._send_key("OP_CL")

    @cmd_wrapper
    async def fast_forward(self):
        return await self._send_key("CUE")

    @cmd_wrapper
    async def rewind(self):
        return await self._send_key("REV")
