# Patching the Panasonic firmware
The player needs to be patched in order to have network commands available (and other features such as region free). 

Principle : you will need a USB flashdrive that will be created from a supplied Ubuntu virtual machine and patch files 
This requires some knowledge so do it at your own risks !

The full procedure is described here : [AVSForum](https://www.avforums.com/threads/lets-try-again-to-put-the-free-in-regionfreedom.2441584/page-69#post-32660031)
You will need a PC or a Mac with an intel based CPU (the supplied VM is a x86 Linux Ubuntu).

The password is the same for unzipping, or root password of the vm : `lulu`

Here are the step by steps patch the firmware

## Backup the current firmware

1. Download the Ubuntu modified virtual machine from the link inside the post : you can also build your own one as described at the [end of this page](#create-own-ubuntu-vm-to-patch-the-player)
2. Download and install Oracle VirtualBox on your machine
3. Download the patch files from the post : these files should be unzipped from the VM, not from your PC/Mac
 - Patcher file (ex : Patch-Program169-182.7z) : main patch program
 - `drive.img.gz` : drive image for the USB flashdrive
 - Additional (optional) patch file(s) : for ex `patcher_overlay_V1.35.zip` to improve overlay menus (link at the end of the post)
4. Open VirtualBox and open the downloaded and unzipped VM `lubuntu.vbox` from step 1 
5. Modify the VM configuration to add a shared folder between your disk and the VM : in this shared folder you will copy the patcher files
 - Add a shared folder : first field is the folder where your patch files are located on your PC/Mac, second field type in `panasonic` and mounting point field `/panasonic`
 - Open the terminal and run this command : `sudo adduser $USER vboxsf` (password : lulu)
 - Reboot the VM
6. Open the file browser on the VM and go to the folder `/panasonic`. Copy the patch files to a folder in your VM like here `/home/lu/Downloads` (otherwise it won't work if you patch from the shared folder):
   <img width="450" height="400" alt="image" src="https://github.com/user-attachments/assets/2170160a-a83f-466a-a2d2-4b1620c17e7d" />
   <br>Unzip the patcher file `Patch-Program...7z` with the file browser or from terminal `7z x <file.7z>`
7. Where you extracted the patcher, replace the `res/drive.img.gz` file by the one you downloaded in step 3
8. Insert a USB key and launch `./Patcher` script from the patcher directory
9. A popup will show up, then select your USB device in the upper right dropdown and click on `Create USB`
   
<img width="649" height="514" alt="image" src="https://github.com/user-attachments/assets/1ff32caf-3dfe-4c6b-83a2-3017ee6399f0" />

<br>Note : if your USB flashdrive is not visible, go to the VM settings and try #1 add it manually in the list from the USB section (green plus button) and #2 Try USB2 or USB3 controllers (the VM needs to be shutdown)
<img width="800" height="400" alt="image" src="https://github.com/user-attachments/assets/5bbbb090-4578-46e1-98df-65b5dc38a85c" />

~~10. This step caused corrupted backups after, you can skip it) Once the USB is flashed, go into the USB drive from the file browser and overwrite in it the files from the patcher overlay (unzip from the UI not command line because unzip don't support protected password archives : `patcher_overlay_...zip`~~

The next steps will occur between your machine and the player :
1. Insert the USB key in the Panasonic player
2. Turn the Panasonic player on : the next step will make a backup of the firmware on the USB key
3. Then run the `Patcher` script again from your machine and this time click on `Connect` then on `Exec script`
4. Once finished (this will generate dump fma files 1 to 7 and write them into the flashdrive, it will take some time), turn off the player

## Patch the firmware

1. Put the USB back in your computer
2. Optional : you change change the srt (subtitle files) font, browse in the USB key and edit the `0_setup.ini` file
3. In the terminal, go into the USB drive - normally a path like `/media/lu/XXX` - and launch (still `lulu` password for root when requested) :

If a `Checksum error` appears, don't go further : restart the backup step earlier
```bash
cd /media/lu/XXX
sudo bash 2_patch.sh
cp -f 3_write.sh script.sh
```

<img width="500" height="350" alt="image" src="https://github.com/user-attachments/assets/ec2dc712-1e4b-4daa-af11-60d4984679f7" />

4. Remove the USB key and put it back in the Panasonic player and turn it on : sometimes you have to remove electric cord if the connection with the patcher fails.
5. Launch `Patcher` from your computer, connect to the player and click on `Exec script`

**Beware, this step takes more than 20 minutes. Try to move arrow keys with your Panasonic remote in the meantime to prevent sleep.**



## Create own Ubuntu VM to patch the Player

An Ubuntu linux x86-64 system is necessary to patch the player : either use the VM from the supplied link or build your own one like here. The Linux system needs to be updated with additional libraries to make the patcher program work.

Download Ubuntu VDI image for VirtualBox such as https://www.osboxes.org/ubuntu/

Install the following packages :
```
sudo apt-get install 7-zip
sudo apt-get install libboost-program-options-dev
```

Edit $HOME/.basrhc profile file and add :
`export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib/x86_64-linux-gnu`

Switch to root user `su - root` and copy the following files from the lib subfolder of the patch program folder into the `/usr/lib/x86_64-linux-gnu` folder : 
<img width="972" height="26" alt="image" src="https://github.com/user-attachments/assets/3ebad0ca-9916-4fd6-a279-d9229c01b580" />
These shared libraries are no longer available on the repository and are necessary to make the `Patcher` create the disk image

The `Patcher` program should work correctly


### Optional : install VirtualBox addon package

This package lets copy/paste and improve integration between host and VM
```
sudo apt-get install virtualbox-guest-additions-iso
cd /media/osboxes/VBox*
sudo ./VBoxLinuxAdditions.run
```
