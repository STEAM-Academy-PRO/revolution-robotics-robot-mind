How to create a new self-hosted runner
======================================

> The runner does not seem to work on the old Pi Zero W, you need to use a W2.

- Make sure you have the latest OS image flashed.
- For your sanity, disconnect the LED board from the carrier PCBA. You may also want to desolder the battery.
- [Connect the brain to wifi](./pi/connect-ssh.md#how-to-enable-wifi)
- SSH into the robot you want to use
  - Modify the Pi's hostname:
    - `sudo nano /etc/hostname`
    - `sudo nano /etc/hosts`
  - Run `sudo timedatectl set-ntp true` to update the Pi's clock
  - You may want to disable the `revvy` service, but you don't have to
- Go to https://github.com/STEAM-Academy-PRO/revolution-robotics-robot-mind/settings/actions/runners
  - Click the `New self-hosted runner` button
  - Select `Linux` and `ARM` (NOT `ARM64`)
  - Follow the Download and Configure instructions
  - Follow [these instructions](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/configuring-the-self-hosted-runner-application-as-a-service#installing-the-service) to auto-start the runner
  - `sudo ./svc.sh start`
