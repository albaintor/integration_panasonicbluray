# Panasonic Bluray integration for Remote Two

Using [uc-integration-api](https://github.com/aitatoi/integration-python-library)

The driver discovers Panasonic Bluray players on the network. A media player and a remote entity are exposed to the core.
The remote entity su

Supported attributes:

- State (on, off, playing, paused, unknown)
- Media position
- Media duration

Supported commands for media player :

- Turn on
- Turn off
- Toggle on/off
- Next / previous chapter
- Fast forward / rewind
- Play/pause
- Stop
- Title menu, main menu, popup menu
- Direction pad
- Digits
- Audio stream switching
- ...
- Simple commands

Supported commands for remote entity :
- Send command
- Send command sequence
- Predefined buttons mapping
- Predefined UI mapping

## Prerequisites
All players supported by the Panasonic Blu-ray Remote 2012 Android app should be supported; i.e. DMP-BDT120, DMP-BDT220, DMP-BDT221, DMP-BDT320, DMP-BDT500 and DMP-BBT01 devices.

Newer players with "UB" prefixes (UB-420, UB-820, and UB-9000) support a (very) limited set of functions
To make it work with latest UHD bluray players (such as UB820), you will have to enable voice control in the network menu AND to patch the Panasonic firmware (not an easy procedure).
More information on [AVSForum](https://www.avforums.com/threads/lets-try-again-to-put-the-free-in-regionfreedom.2441584/post-31906429)
Tested correctly on Panasonic UB820.

## Usage

### Setup

- Requires Python 3.11
- Install required libraries:  
  (using a [virtual environment](https://docs.python.org/3/library/venv.html) is highly recommended)

```shell
pip3 install -r requirements.txt
```

For running a separate integration driver on your network for Remote Two, the configuration in file
[driver.json](driver.json) needs to be changed:

- Set `driver_id` to a unique value, `uc_panasonicbluray_driver` is already used for the embedded driver in the firmware.
- Change `name` to easily identify the driver for discovery & setup with Remote Two or the web-configurator.
- Optionally add a `"port": 8090` field for the WebSocket server listening port.
    - Default port: `9091`
    - Also overrideable with environment variable `UC_INTEGRATION_HTTP_PORT`

### Run

```shell
python3 intg-panasonicbluray/driver.py
```

See
available [environment variables](https://github.com/unfoldedcircle/integration-python-library#environment-variables)
in the Python integration library to control certain runtime features like listening interface and configuration
directory.

### Available commands for the remote entity

Available commands for remote entity :

| Command          | Description        |
|------------------|--------------------|
| POWERON          | Power on           |
| POWEROFF         | Power off          |
| POWER            | Power toggle       |
| OP_CL            | Open/close         |
| PLAYBACK         | Play               |
| PAUSE            | Pause              |
| STOP             | Stop               |
| SKIPFWD          | Next chapter       |
| SKIPREV          | Previous chapter   |
| REV              | Rewind             |
| CUE              | Fast forward       |
| D0               | 0 (-,)             |
| D1               | 1 (@.)             |
| D2               | 2 (ABC)            |
| D3               | 3 (DEF)            |
| D4               | 4 (GHI)            |
| D5               | 5 (JKL)            |
| D6               | 6 (MNO)            |
| D7               | 7 (PQRS)           |
| D8               | 8 (TUV)            |
| D9               | 9 (WXYZ)           |
| D12              | 12                 |
| SHARP            | # ([_])            |
| CLEAR            | * or cancel        |
| UP               | Up                 |
| DOWN             | Down               |
| LEFT             | Left               |
| RIGHT            | Right              |
| SELECT           | Select             |
| RETURN           | Return             |
| EXIT             | Exit               |
| MLTNAVI          | Home               |
| DSPSEL           | Status             |
| TITLE            | Title              |
| MENU             | Menu               |
| PUPMENU          | Popup Menu         |
| SHFWD1           | SHFWD1             |
| SHFWD2           | SHFWD2             |
| SHFWD3           | SHFWD3             |
| SHFWD4           | SHFWD4             |
| SHFWD5           | SHFWD5             |
| SHREV1           | SHREV1             |
| SHREV2           | SHREV2             |
| SHREV3           | SHREV3             |
| SHREV4           | SHREV4             |
| SHREV5           | SHREV5             |
| JLEFT            | JLEFT              |
| JRIGHT           | JRIGHT             |
| RED              | Red                |
| BLUE             | Blue               |
| GREEN            | Green              |
| YELLOW           | Yellow             |
| NETFLIX          | Netflix            |
| SKYPE            | Skype              |
| V_CAST           | V_CAST             |
| 3D               | 3D                 |
| NETWORK          | Network            |
| AUDIOSEL         | Audio language     |
| KEYS             | Keys               |
| CUE              | Cue                |
| CHROMA           | Chrooma            |
| MNBACK           | Manual skip -10s   |
| MNSKIP           | Manual skip +60s   |
| 2NDARY           | 2NDARY             |
| PICTMD           | PICTMD             |
| DETAIL           | DETAIL             |
| RESOLUTN         | Resolution         |
| OSDONOFF         | OSD ON/OFF         |
| P_IN_P           | Picture in picture |
| PLAYBACKINFO     | Playback Info	     |
| CLOSED_CAPTION   | Closed Caption     |
| TITLEONOFF       | Subtitle           |
| HDR_PICTUREMODE  | HDR Picture Mode   |
| PICTURESETTINGS  | Picture Setting    |
| SOUNDEFFECT      | Soud Effect        |
| HIGHCLARITY      | High clarity       |
| SKIP_THE_TRAILER | Skip The Trailer   |
| MIRACAST         | Mirroring          |

## Build self-contained binary for Remote Two

After some tests, turns out python stuff on embedded is a nightmare. So we're better off creating a single binary file
that has everything in it.

To do that, we need to compile it on the target architecture as `pyinstaller` does not support cross compilation.

### x86-64 Linux

On x86-64 Linux we need Qemu to emulate the aarch64 target platform:

```bash
sudo apt install qemu binfmt-support qemu-user-static
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

Run pyinstaller:

```shell
docker run --rm --name builder \
    --platform=aarch64 \
    --user=$(id -u):$(id -g) \
    -v "$PWD":/workspace \
    docker.io/unfoldedcircle/r2-pyinstaller:3.11.6  \
    bash -c \
      "python -m pip install -r requirements.txt && \
      pyinstaller --clean --onefile --name intg-panasonicbluray intg-panasonicbluray/driver.py"
```

### aarch64 Linux / Mac

On an aarch64 host platform, the build image can be run directly (and much faster):

```shell
docker run --rm --name builder \
    --user=$(id -u):$(id -g) \
    -v "$PWD":/workspace \
    docker.io/unfoldedcircle/r2-pyinstaller:3.11.6  \
    bash -c \
      "python -m pip install -r requirements.txt && \
      pyinstaller --clean --onefile --name intg-panasonicbluray intg-panasonicbluray/driver.py"
```

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the
[tags and releases in this repository](https://github.com/albaintor/integration-panasonicbluray/releases).

## Changelog

The major changes found in each new release are listed in the [changelog](CHANGELOG.md)
and under the GitHub [releases](https://github.com/albaintor/integration-panasonicbluray/releases).

## Contributions

Please read our [contribution guidelines](CONTRIBUTING.md) before opening a pull request.

## License

This project is licensed under the [**Mozilla Public License 2.0**](https://choosealicense.com/licenses/mpl-2.0/).
See the [LICENSE](LICENSE) file for details.
