How to connect to the brain
===========================

You have two options:
- USB: needs more setup on your PC, but less on the brain
- Wifi: needs more setup on the brain, but less on your PC

In both cases, the login on the brain is:
- user: `pi`
- password: `123`

Windows
-------

- Make sure the robot is turned on
- Connect the robot to your computer via a USB cable.
- Open Device Manager and make sure it shows up under Network Interfaces as `USB Ethernet/RNDIS Gadget`
  - If not, unplug the robot and observe that the device list flashes once.
  - If the device list does not flash, your computer does not see the robot. Replace the USB cable with a new one and try again.
  - If the device list flashes, but you don't see the `USB Ethernet/RNDIS Gadget`, you'll need to install drivers from https://www.catalog.update.microsoft.com/Search.aspx?q=USB%20RNDIS%20Gadget. Make sure to select `	Acer Incorporated. - Other hardware - USB Ethernet/RNDIS Gadget	Windows 7,Windows 8,Windows 8.1 and later drivers`.

- Download and install putty
- In the host field, enter `pi@raspberrypi.local`. Make sure port is 22 and that SSH is selected.
- Save the connection for later use. Enter a name under Saved Sessions and press Save.
- Press Open to connect.
- If asked, accept the fingerprint.
- To access the filesystem, use WinSCP or the SecureFTP TotalCommander plugin.

Linux
-----

- figure out the IP address (TODO: fix auto dhcp IP address or document enable Bonjour service for linux)
- `ssh pi@some.ip`

- find the Pi on the network:
- `arp | grep -v incomplete` or `nmap -sn $(ip route | awk '/default/ {print $3}')/24 -p 22`
- `ssh pi@found-ip`
- mount the file system to your local drive!
- ease your way in with `ssh-copy-id pi@found-ip` so you do not need a password.

How to enable Wifi
------------------

You may want to SSH into the brain over Wifi instead of USB. Here's how to set up the brain:

- remove the SD card from brain, insert into laptop
- make sure `dtoverlay=pi3-disable-wifi` is **NOT** present or commented out in `config.txt`
- edit `wpa_supplicant.conf` on the boot partition with the following content with your wifi router data:

```
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=GB

network={
     ssid="your_network_name"
     psk="your_wifi_password"
     key_mgmt=WPA-PSK
}
```

- place the SD card back into the brain, start the brain
