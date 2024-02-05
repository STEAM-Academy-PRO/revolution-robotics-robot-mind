Setting up the C development environment
========================================

Dev container (recommended)
---------------------------

- [Share GitHub credentials with the container](https://code.visualstudio.com/remote/advancedcontainers/sharing-git-credentials)

Local development
-----------------

### Tools required

- git
- ARM GCC, make
- VS Code if you intend to keep your sanity
- [Debugger for probe-rs](https://marketplace.visualstudio.com/items?itemName=probe-rs.probe-rs-debugger) and [probe-rs](https://probe.rs)
- python 3.7 or newer

### Set up compiler

> Latest gcc does not compile, until fixed, you will need the `gcc-arm-none-eabi-10.3-2021.10` version

#### Linux

- `sudo apt install build-essential`
- Download and extract [`gcc-arm-none-eabi-10.3-2021.10`](https://developer.arm.com/downloads/-/gnu-rm) to `/usr/share/gcc-arm/`

#### Windows

- Download and extract [`gcc-arm-none-eabi-10.3-2021.10`](https://developer.arm.com/downloads/-/gnu-rm) to `C:\gcc\`.
- Download the `Binaries` and `Dependencies` from http://gnuwin32.sourceforge.net/packages/make.htm
  - Extract the downloaded directories to a place of your choice. (For example, C:\gnu\make)
  - Add the bin folder of the extracted archive to your `$PATH`.
- Use `zadig` to replace the jlink drivers with WinUSB

### Set up project

- open a command line in the project directory
- Run command `python -m venv venv` to create new virtual environment in the `venv` directory
- Activate virtual environment by running
  - Windows: `.\venv\Scripts\activate`
  - Linux: `source ./venv/bin/activate`
- Run command `pip install -r tools/requirements.txt`
