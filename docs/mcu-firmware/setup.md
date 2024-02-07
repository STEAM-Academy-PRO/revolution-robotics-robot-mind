Setting up the C development environment
========================================

Tools required
--------------

 - git
 - ARM GCC, make
 - VS Code
 - python 3.7 or newer

Set up compiler
---------------

### Linux

- `sudo apt install build-essential`
- Download and extract [`gcc-arm-none-eabi-10.3-2021.10`](https://developer.arm.com/downloads/-/gnu-rm) to `/usr/share/gcc-arm/`

### Windows

- Download and extract [`gcc-arm-none-eabi-10.3-2021.10`](https://developer.arm.com/downloads/-/gnu-rm) to `C:\gcc\`.
- Download the `Binaries` and `Dependencies` from http://gnuwin32.sourceforge.net/packages/make.htm
  - Extract the downloaded directories to a place of your choice. (For example, C:\gnu\make)
  - Add the bin folder of the extracted archive to your `$PATH`.

Set up a debugger
-----------------

Choose one of the following:

### J-Link tools and GDB

- Download JLink packet from the segger website. It is possible to download package for Windows and Linux as well.
- Now you have to install these extensions in VSCode: C/C++ (intellisense) and Cortex-Debug
- You have to set toolchain path in Cortex-Debug ext. settings or in your `settings.json`.
- Check that gdb and gcc run without problems because on recent version of Ubuntu it require obsolete libraries (for 23.10 you should install libncurses5 manually)
- In VSCode, select the `Run and Debug` sidebar, and select `Cortex Debug (JLink)`

### probe-rs

- [Debugger for probe-rs](https://marketplace.visualstudio.com/items?itemName=probe-rs.probe-rs-debugger) and [probe-rs](https://probe.rs)
- Use `zadig` to replace the jlink drivers with WinUSB
- In VS Code, select the `Run and Debug` sidebar, and select `probe_rs run`

Set up project
--------------

 - open a command line in the project directory
 - Run command `python -m venv venv` to create new virtual environment in the `venv` directory
 - Activate virtual environment by running
   - Windows: `.\venv\Scripts\activate`
   - Linux: `source ./venv/bin/activate`
 - Run command `pip install -r tools/requirements.txt`
