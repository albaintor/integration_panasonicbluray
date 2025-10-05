# Panasonic Bluray integration for Remote Two/3

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
Detailed information on [AVSForum](https://www.avforums.com/threads/lets-try-again-to-put-the-free-in-regionfreedom.2441584/page-69#post-32660031)
Tested correctly on my Panasonic UB820.

For more information on available commands see [this page](https://next.openhab.org/addons/bindings/panasonicbdp/)


## Installation on the remote (recommended)

- First [go to the release section](https://github.com/albaintor/integration_panasonicbluray/releases) and download the `xxx_aarch64-xxx.tar.gz` file
- On the Web configurator of your remote, go to the `Integrations` tab, click on `Add new` and select `Install custom`
- Select the downloaded file in first step and wait for the upload to finish
- Once uploaded, the new integration should appear in the list : click on it and select `Start setup`
- The Bluray player must be running for setup


## Patching the Panasonic firmware
The player needs to be patched in order to have commands available (and other features such as region free). 

Principle : you will need a USB flashdrive that will be created from a supplied Ubuntu virtual machine and patch files 
This requires some knowledge so do it at your own risks !

The full procedure is described here : [AVSForum](https://www.avforums.com/threads/lets-try-again-to-put-the-free-in-regionfreedom.2441584/page-69#post-32660031)
You will need a PC or a Mac with an intel based CPU (the supplied VM is a x86 Linux Ubuntu).

The password is the same for unzipping, or root password of the vm : `lulu`

Here are the step by steps patch the firmware :
1. Download the Ubuntu modified virtual machine from the link inside the post
2. Download and install Oracle VirtualBox on your machine
3. Download the patch files from the post : these files should be unzipped from the VM, not from your PC/Mac
 - Patcher file (ex : Patch-Program169-182.7z) : main patch program
 - `drive.img.gz` : drive image for the USB flashdrive
 - Additional (optional) patch file(s) : for ex `patcher_overlay_V1.35.zip` to improve overlay menus (link at the end of the post)
4. Open VirtualBox and open the downloaded and unzipped VM `lubuntu.vbox` from step 1 
5. Modify the VM configuration to add a shared folder between your disk and the VM : in this shared folder you will copy the patcher files
6. Unzip the patcher file `Patch-Program...7z` (with the file browser or from terminal `7z x <file.7z>`) : unzip to another folder than the shared folder otherwise it won't work
7. Where you extracted the patcher, replace the `res/drive.img.gz` file by the one you downloaded in step 3
8. Insert a USB key and launch `./Patcher` script from the patcher directory
9. A popup will show up, then select your USB device in the upper right dropdown and click on `Create USB`
9. (this step caused corrupted backups after, you can skip it) Once the USB is flashed, go into the USB drive from the file browser and overwrite in it the files from the patcher overlay (unzip from the UI not command line because unzip don't support protected password archives) : `patcher_overlay_...zip`

The next steps will occur between your machine and the player :
1. Insert the USB key in the Panasonic player
2. Turn the Panasonic player on : the next step will make a backup of the firmware on the USB key
3. Then run the `Patcher` script again from your machine and this time click on `Connect` then on `Exec script`
4. Once finished (this will generate dump fma files 1 to 7, it will take some time), turn off the player
5. Put the USB back in your computer
6. Optional : you change change the srt (subtitle files) font, browse in the USB key and edit the `0_setup.ini` file
7. In the terminal, go into the USB drive (normally `/media/lu/XXX`) and launch (still `lulu` password for root) :
```bash
sudo bash 2_patch.sh
cp -f 3_write.sh script.sh
```
8. If a `Checksum error` appears, don't go further : restart from the previous step 8
9. Remove the USB key and put it back in the Panasonic player and turn it on : sometimes you have to remove electric cord if the connection with the patcher fails.
10. Launch `Patcher` from your computer, connect to the player and click on `Exec script` : beware, this step takes more than 20 minutes. Try to move arrow keys in the meantime to prevent sleep.


## Installation as external integration

- Requires Python 3.11
- Install required libraries:  
  (using a [virtual environment](https://docs.python.org/3/library/venv.html) is highly recommended)

```shell
pip3 install -r requirements.txt
```

For running a separate integration driver on your network for Remote Two, the configuration in file
[driver.json](driver.json) needs to be changed:

- Set `driver_id` to a unique value, `panasonicbluray_driver` is already used for the embedded driver in the firmware.
- Change `name` to easily identify the driver for discovery & setup with Remote Two or the web-configurator.
- Optionally add a `"port": 8090` field for the WebSocket server listening port.
    - Default port: `9091`
    - Also overrideable with environment variable `UC_INTEGRATION_HTTP_PORT`

### Run

```shell
python3 src/driver.py
```

See
available [environment variables](https://github.com/unfoldedcircle/integration-python-library#environment-variables)
in the Python integration library to control certain runtime features like listening interface and configuration
directory.

## Available commands for the remote entity

Note that 2 entities are exposed by the integration : `Media player` and `Remote` entities.
Media player should cover most needs with its integrated commands.
Otherwise remote entity expose custom commands that are listed below.
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
