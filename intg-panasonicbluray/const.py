from datetime import timedelta

__version__ = "1.0.0"

from enum import IntEnum, Enum

import ucapi
from ucapi.media_player import Commands
from ucapi.ui import DeviceButtonMapping, Buttons, UiPage


class States(IntEnum):
    """State of a connected device."""

    UNKNOWN = 0
    UNAVAILABLE = 1
    OFF = 2
    ON = 3
    PLAYING = 4
    PAUSED = 5
    STOPPED = 6


# Mapping of a device state to a media-player entity state
MEDIA_PLAYER_STATE_MAPPING: dict[States, ucapi.media_player.States] = {
    States.ON: ucapi.media_player.States.ON,
    States.OFF: ucapi.media_player.States.OFF,
    States.PAUSED: ucapi.media_player.States.PAUSED,
    States.STOPPED: ucapi.media_player.States.PAUSED,
    States.PLAYING: ucapi.media_player.States.PLAYING,
    States.UNAVAILABLE: ucapi.media_player.States.UNAVAILABLE,
    States.UNKNOWN: ucapi.media_player.States.UNKNOWN,
}

USER_AGENT = 'MEI-LAN-REMOTE-CALL'
SCAN_INTERVAL = timedelta(seconds=10)
MIN_TIME_BETWEEN_SCANS = SCAN_INTERVAL
MIN_TIME_BETWEEN_FORCED_SCANS = timedelta(seconds=1)
DEFAULT_NAME = "panasonicbluray"

# Known key commands
KEYS = ['POWER', 'OP_CL', 'POWERON', 'POWEROFF'
        'PLAYBACK', 'PAUSE', 'STOP', 'SKIPFWD', 'SKIPREV', 'REV',
        'D0', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D12',
        'SHARP',  # '#'
        'CLEAR',  # '*' /  CANCEL
        'UP', 'DOWN', 'LEFT', 'RIGHT', 'SELECT', 'RETURN', 'EXIT',
        'MLTNAVI',  # HOME
        'DSPSEL',  # STATUS
        'TITLE', 'MENU', 'PUPMENU',
        'SHFWD1', 'SHFWD2', 'SHFWD3', 'SHFWD4', 'SHFWD5',
        'SHREV1', 'SHREV2', 'SHREV3', 'SHREV4', 'SHREV5',
        'JLEFT', 'JRIGHT',
        'RED', 'BLUE', 'GREEN', 'YELLOW',
        'NETFLIX', 'SKYPE', 'V_CAST', '3D', 'NETWORK', 'AUDIOSEL',
        'KEYS', 'CUE', 'CHROMA',
        'MNBACK', 'MNSKIP', '2NDARY', 'PICTMD', 'DETAIL', 'RESOLUTN',
        # Playback view?
        'OSDONOFF', 'P_IN_P', 'PLAYBACKINFO', 'HDR_PICTUREMODE', 'PICTURESETTINGS',
        'HIGHCLARITY', 'SKIP_THE_TRAILER', 'MIRACAST', 'PLAYBACKINFO', 'TITLEONOFF',
        'CLOSED_CAPTION', 'SETUP'
        ]

PANASONIC_SIMPLE_COMMANDS = {
    "MENU_HOME": "MLTNAVI",
    "MODE_STATUS": "DSPSEL",
    "MODE_EXIT": "EXIT",
    "MENU_NETWORK": "NETWORK",
    "MENU_PICTURE": "PICTURESETTINGS",
    "MENU_PLAYBACKINFO": "PLAYBACKINFO",
    "MODE_SUBTITLES": "TITLEONOFF",
    "MODE_CLOSED_CAPTION": "CLOSED_CAPTION",
    "MODE_HDR_PICTURE": "HDR_PICTUREMODE",
    "MODE_MIRACAST": "MIRACAST",
    "MODE_HIGHCLARITY": "HIGHCLARITY",
    "MODE_SKIP_TRAILER": "SKIP_THE_TRAILER",
    "MODE_SOUNDEFFECT": "SOUNDEFFECT"
}

class PlayerVariant(Enum):
    AUTO = 1
    BD = 2
    UB = 3


PANASONIC_REMOTE_BUTTONS_MAPPING: [DeviceButtonMapping] = [
    {"button": Buttons.BACK, "short_press": {"cmd_id": "RETURN"}},
    {"button": Buttons.HOME, "short_press": {"cmd_id": "MENU"}},
    {"button": Buttons.CHANNEL_DOWN, "short_press": {"cmd_id": "SKIPREV"}},
    {"button": Buttons.CHANNEL_UP, "short_press": {"cmd_id": "SKIPFWD"}},
    {"button": Buttons.DPAD_UP, "short_press": {"cmd_id": "UP"}},
    {"button": Buttons.DPAD_DOWN, "short_press": {"cmd_id": "DOWN"}},
    {"button": Buttons.DPAD_LEFT, "short_press": {"cmd_id": "LEFT"}},
    {"button": Buttons.DPAD_RIGHT, "short_press": {"cmd_id": "RIGHT"}},
    {"button": Buttons.DPAD_MIDDLE, "short_press": {"cmd_id": "SELECT"}},
    {"button": Buttons.PLAY, "short_press": {"cmd_id": "PAUSE"}},
    {"button": Buttons.PREV, "short_press": {"cmd_id": "REV"}},
    {"button": Buttons.NEXT, "short_press": {"cmd_id": "CUE"}},
    {"button": Buttons.VOLUME_UP, "short_press": {"cmd_id": Commands.VOLUME_UP}},
    {"button": Buttons.VOLUME_DOWN, "short_press": {"cmd_id": Commands.VOLUME_DOWN}}
]

PANASONIC_REMOTE_UI_PAGES: [UiPage] = [
    {
        "page_id": "Panasonic commands",
        "name": "Panasonic commands",
        "grid": {"width": 4, "height": 6},
        "items": [
            {
                "command": {
                    "cmd_id": "remote.send",
                    "params": {"command": "PLAYBACKINFO", "repeat": 1}
                },
                "icon": "uc:info",
                "location": {
                    "x": 0,
                    "y": 0
                },
                "size": {
                    "height": 1,
                    "width": 1
                },
                "type": "icon"
            },
            {
                "command": {
                    "cmd_id": "remote.send",
                    "params": {"command": "AUDIOSEL", "repeat": 1}
                },
                "icon": "uc:language",
                "location": {
                    "x": 1,
                    "y": 0
                },
                "size": {
                    "height": 1,
                    "width": 1
                },
                "type": "icon"
            },
            {
                "command": {
                    "cmd_id": "remote.send",
                    "params": {"command": "CLOSED_CAPTION", "repeat": 1}
                },
                "icon": "uc:cc",
                "location": {
                    "x": 2,
                    "y": 0
                },
                "size": {
                    "height": 1,
                    "width": 1
                },
                "type": "icon"
            },
            {
                "command": {
                    "cmd_id": "remote.send",
                    "params": {"command": "TITLEONOFF", "repeat": 1}
                },
                "text": "Toggle subtitles",
                "location": {
                    "x": 3,
                    "y": 0
                },
                "size": {
                    "height": 1,
                    "width": 1
                },
                "type": "text"
            },
            {
                "command": {
                    "cmd_id": "remote.send",
                    "params": {"command": "3D", "repeat": 1}
                },
                "text": "3D",
                "location": {
                    "x": 0,
                    "y": 1
                },
                "size": {
                    "height": 1,
                    "width": 1
                },
                "type": "text"
            },
            {
                "command": {
                    "cmd_id": "remote.send",
                    "params": {"command": "OP_CL", "repeat": 1}
                },
                "text": "Eject",
                "location": {
                    "x": 1,
                    "y": 1
                },
                "size": {
                    "height": 1,
                    "width": 1
                },
                "type": "text"
            },
            {
                "command": {
                    "cmd_id": "remote.send",
                    "params": {"command": "TITLE", "repeat": 1}
                },
                "text": "Title",
                "location": {
                    "x": 2,
                    "y": 1
                },
                "size": {
                    "height": 1,
                    "width": 1
                },
                "type": "text"
            },
            {
                "command": {
                    "cmd_id": "remote.send",
                    "params": {"command": "PUPMENU", "repeat": 1}
                },
                "icon": "uc:menu",
                "location": {
                    "x": 3,
                    "y": 5
                },
                "size": {
                    "height": 1,
                    "width": 1
                },
                "type": "icon"
            },
        ]
    },
    {
        "page_id": "Panasonic numbers",
        "name": "Panasonic numbers",
        "grid": { "height": 4, "width": 3 },
        "items": [{
            "command": {
                "cmd_id": "remote.send",
                "params": {"command": "D1", "repeat": 1}
            },
            "location": {
                "x": 0,
                "y": 0
            },
            "size": {
                "height": 1,
                "width": 1
            },
            "text": "1",
            "type": "text"
        }, {
            "command": {
                "cmd_id": "remote.send",
                "params": {"command": "D2", "repeat": 1}
            },
            "location": {
                "x": 1,
                "y": 0
            },
            "size": {
                "height": 1,
                "width": 1
            },
            "text": "2",
            "type": "text"
        }, {
            "command": {
                "cmd_id": "remote.send",
                "params": {"command": "D3", "repeat": 1}
            },
            "location": {
                "x": 2,
                "y": 0
            },
            "size": {
                "height": 1,
                "width": 1
            },
            "text": "3",
            "type": "text"
        }, {
            "command": {
                "cmd_id": "remote.send",
                "params": {"command": "D4", "repeat": 1}
            },
            "location": {
                "x": 0,
                "y": 1
            },
            "size": {
                "height": 1,
                "width": 1
            },
            "text": "4",
            "type": "text"
        }, {
            "command": {
                "cmd_id": "remote.send",
                "params": {"command": "D5", "repeat": 1}
            },
            "location": {
                "x": 1,
                "y": 1
            },
            "size": {
                "height": 1,
                "width": 1
            },
            "text": "5",
            "type": "text"
        }, {
            "command": {
                "cmd_id": "remote.send",
                "params": {"command": "D6", "repeat": 1}
            },
            "location": {
                "x": 2,
                "y": 1
            },
            "size": {
                "height": 1,
                "width": 1
            },
            "text": "6",
            "type": "text"
        }, {
            "command": {
                "cmd_id": "remote.send",
                "params": {"command": "D7", "repeat": 1}
            },
            "location": {
                "x": 0,
                "y": 2
            },
            "size": {
                "height": 1,
                "width": 1
            },
            "text": "7",
            "type": "text"
        }, {
            "command": {
                "cmd_id": "remote.send",
                "params": {"command": "D8", "repeat": 1}
            },
            "location": {
                "x": 1,
                "y": 2
            },
            "size": {
                "height": 1,
                "width": 1
            },
            "text": "8",
            "type": "text"
        }, {
            "command": {
                "cmd_id": "remote.send",
                "params": {"command": "D9", "repeat": 1}
            },
            "location": {
                "x": 2,
                "y": 2
            },
            "size": {
                "height": 1,
                "width": 1
            },
            "text": "9",
            "type": "text"
        }, {
            "command": {
                "cmd_id": "remote.send",
                "params": {"command": "D0", "repeat": 1}
            },
            "location": {
                "x": 1,
                "y": 3
            },
            "size": {
                "height": 1,
                "width": 1
            },
            "text": "0",
            "type": "text"
        }
        ]
    }
]