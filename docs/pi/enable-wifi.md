How to enable Wifi
==================

You may want to SSH into the brain over Wifi instead of USB. Here's how to set up the brain:

- remove SD card from brain, insert to laptop
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

- place back SD card to brain, start the brain
