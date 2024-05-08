Set up the project
==================

- Check out the sources of `pi-firmware` to a directory of your choice.
- Create a python virtual environment in the source directory by running `python -m venv venv`
- Active the virtual environment by running
  - Windows: `.\venv\Scripts\activate`
  - Linux: `source ./venv/bin/activate`
- Install the required packages by running `pip install -r install/requirements_dev.txt`

Recommended Dev Env
-------------------

Use VSCode, open this folder.
- Copy & rename your `settings.example.json` file within your `.vscode` folder
- set your `target` to the IP address of your brain's PI if you are using your wifi for debugging
  - (sometimes it works even through the wifi router is hosting a bonjour service)

VSCode setup
------------

- Enable auto imports in settings: `"python.analysis.autoImportCompletions": true`
- install recommended extensions!
- make sure the tests on the side showed up

Debugging & Run
---------------

- open a VSCode terminal
- from this dir, run `./debug`
  - This will not remember your password. Run `ssh-copy-id pi@raspberrypi.local` to do so.
  - If you get loud complaints about changed fingerprints, run `ssh-keygen -R raspberrypi.local`
- for attaching debugger, run `./debug 1`
- When says: Waiting for debugger, hit `F5` - `Attach PI Debugger` in the main window
- if it says: "client port not open" just wait for a few more seconds and try again
- happy debugging!

SD Card write protection
------------------------

Remove default write protection:
- ssh into the brain
```bash
# Temporary:
sudo mount -o rw,remount /
```

```bash
# Permanent
sudo nano /etc/fstab

# in the line of root (/) change `ro` to `rw`
```