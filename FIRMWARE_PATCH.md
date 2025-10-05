# Patching the Panasonic firmware
The player needs to be patched in order to have network commands available (and other features such as region free). 

Principle : you will need a USB flashdrive that will be created from a supplied Ubuntu virtual machine and patch files 
This requires some knowledge so do it at your own risks !

The full procedure is described here : [AVSForum](https://www.avforums.com/threads/lets-try-again-to-put-the-free-in-regionfreedom.2441584/page-69#post-32660031)
You will need a PC or a Mac with an intel based CPU (the supplied VM is a x86 Linux Ubuntu).

The password is the same for unzipping, or root password of the vm : `lulu`

Here are the step by steps patch the firmware :
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
