Set up the project
==================

- Check out the sources of `pi-firmware` to a directory of your choice.
- Create a python virtual environment in the source directory by running `python -m venv venv`
- Active the virtual environment by running
  - Windows: `.\venv\Scripts\activate`
  - Linux: `source ./venv/bin/activate`
- Install the required packages by running `pip install -r install/requirements_test.txt`

Recommended Dev Env
-------------------

Use VSCode, open this folder.
Create a `target` file and add the IP address of the brain. (bonjour: `raspberrypi.local` or e.g. `192.168.0.123` for wifi)

VSCode setup
------------

- Enable auto imports in settings: `"python.analysis.autoImportCompletions": true`
- install recommended extensions!

Debugging
---------

- from this dir, run `./debug`
- for attaching debugger, run `./debug 1`
- When says: Waiting for debugger, run 
- configure your `launch.json` to the proper IP

```json
{
  "name": "Attach PI Debugger",
  "type": "python",
  "request": "attach",
  "connect": {
    "host": "192.168.0.X",
    "port": 5678
  }
}
```