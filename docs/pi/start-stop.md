How to start/stop/restart the framework service
===============================================

> Unless otherwise specified, the paths and commands used here are local to the brain.
> [How to SSH into the brain?](ssh-usb.md)

After startup, the framework service is already running. If you want to modify it, or run a tool
script or other scripts that work with the framework, you'll need to stop the service before
starting your script, or restart it after a modification.

To control the framework service, use these commands:

 - Stop: `sudo systemctl stop revvy` or `stop`
 - Start: `sudo systemctl start revvy` or `start`
 - Restart: `sudo systemctl restart revvy`

Which package is started?
-------------------------

The loader will scan each package in `~/RevvyFramework/user/packages`. The folder name of
these packages does not matter, the loader will read the version information from `manifest.json`.

The versons are in the format of `major.minor.patch-suffix`, and are compared with `major` first,
`patch` last. `.patch` is optional and considered `0` if not set. `-suffix` is optional and ignored.

If `~/RevvyFramework/user/packages` contains no packages that can be started, the loader
will start the default installation from `~/RevvyFramework/default/packages`.

About the integrity protection and modifications
------------------------------------------------

After startup the framework scans for unintended modifications in the source code. This is done by
comparing the checksum of the individual files to those contained in the `manifest.json` file. If a 
file is not listed in the manifest, it is ignored. If a checksum does not match, the framework
exits, deletes the "damaged" package and if possible, an older one is then started.

Because of this, if you intend to modify a file, you need to either update the manifest with the new
MD5 checksum, or remove the modified file from the manifest.

Only the packages located under `~/RevvyFramework/user/packages` can be modified, other parts of the
filesystem are read-only.

Debugging your code
-------------------

### Running your code locally

If you want to start the framework, but not the service (for example, you want to observe console
output), enter the framework directory by running `cd RevvyFramework` and start by executing
`python3 launch_revvy.py`. To exit, press Enter.

> Be careful!
>
> This process is meant to start packages that were generated using `dev_tools.generate_package`.
> If you modified the package in any way, delete the modified files' hash from the package's
> `manifest.json`. If you don't do this, the loader will treat this as an error and
> delete your package.

### Remote debugging

> This section is Linux-specific

On your PC, open `pi-firmware` in VS Code, open a Terminal tab and run `./debug 1`. After the script
prints `Launch the 'Attach PI Debugger in VSCode!'` you can press `F5` to attach the remote
debugger.
