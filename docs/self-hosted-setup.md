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
  - Follow the Download and Configure instructions. When asked for a label, enter `silent-runner` for the per-PR HIL tester, and `noisy-runner` for the complete tester robot.
  - Follow [these instructions](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/configuring-the-self-hosted-runner-application-as-a-service#installing-the-service) to auto-start the runner
  - `sudo ./svc.sh start`

# Help, my runner is offline!

Go to https://github.com/STEAM-Academy-PRO/revolution-robotics-robot-mind/settings/actions/runners.
If your runner is `Offline`, but it's powered on and has internet access, the connection to GitHub broke somehow and you'll need to re-register the device.
Unfortunately, this can happen regularly, probably when the runner updates itself.

To verify this state, `cd` into the `actions-runner` folder and run `sudo ./svc.sh status`. If you see the following line, you'll need to re-register:

> Jun 15 11:27:56 revvy-ci runsvc.sh[396]: Failed to create a session. The runner registration has been deleted from the server, please re-configure. [...]

To do so, run the following commands:

```sh
cd actions-runner

# Remove the runner:

sudo ./svc.sh uninstall
./config.sh remove --token [The currently active token read on the GitHub New Runner page]

# Now do the configuration steps:

./config.cmd --url https://github.com/STEAM-Academy-PRO/revolution-robotics-robot-mind --token [The currently active token read on the GitHub New Runner page]
sudo ./svc.sh install
sudo ./svc.sh start
```

If, after doing the above steps, `sudo ./svc.sh status` shows you the following, you'll need to manually reinstall the runner. The removal steps are the same as above.

> Unhandled exception. System.BadImageFormatException: Could not load file or assembly 'System.Net.Http
