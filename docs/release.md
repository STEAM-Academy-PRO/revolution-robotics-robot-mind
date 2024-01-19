How to release a new package
============================

Release a Pi firmware update
----------------------------

- be absolutely sure it works
- create a new tag
- The CI's [release workflow](ci.md#release) will build a release package
- CI will upload the package to the appropriate place(s)

Create a new Pi OS image
------------------------

### For release

- Release a new Pi firmware, as written above
- Update [The OS builder config](https://github.com/STEAM-Academy-PRO/revolution-robotics-pi-os/blob/main/config) with the new Pi firmware **tag**
  - Example: `FIRMWARE_REV=tags/v0.2.0`
- Commit your changes and push to `main`
- Create a new [**pre-release**](https://github.com/STEAM-Academy-PRO/revolution-robotics-pi-os/releases/new)
- Wait for the build to succeed and for the image to appear in the [releases](https://github.com/STEAM-Academy-PRO/revolution-robotics-pi-os/releases)

### For testing

- Create a new branch in the Pi OS repo
- Update [The OS builder config](https://github.com/STEAM-Academy-PRO/revolution-robotics-pi-os/blob/main/config) with the new Pi firmware **revision**
  - Example: `FIRMWARE_REV=12e88a4225bd9a6f00ee611bab5dbed20e3561c9`
- Commit your changes and push
  > Do **not** push to `main`!
- Open a PR. CI will build image & create an artifact. You will be able to download the image from the `Actions` tab, under your branches workflow.
