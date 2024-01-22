Setting up the C development environment
========================================

Tools required
--------------

 - git
 - ARM GCC, make
 - VS Code if you intend to keep your sanity
 - [Debugger for probe-rs](https://marketplace.visualstudio.com/items?itemName=probe-rs.probe-rs-debugger) and [probe-rs](https://probe.rs)

Set up compiler
---------------

> Latest gcc does not compile, until fixed, you will need the `gcc-arm-none-eabi-9-2019-q4-major` version

### Linux

- `sudo apt install build-essential`
- Download and extract [`gcc-arm-none-eabi-9-2019-q4-major`](https://developer.arm.com/downloads/-/gnu-rm) to `/usr/share/gcc-arm/gcc-arm-none-eabi-9-2019-q4-major`
  - Add the `bin` folder to your `$PATH` (`.bashrc`)

### Windows

- Download and extract [`gcc-arm-none-eabi-9-2019-q4-major`](https://developer.arm.com/downloads/-/gnu-rm) to `C:\gcc\gcc-arm-none-eabi-9-2019-q4-major`.
  - Add the `bin` folder to your `$PATH`.
- Download the `Binaries` and `Dependencies` from http://gnuwin32.sourceforge.net/packages/make.htm
  - Extract the downloaded directories to a place of your choice. (For example, C:\gnu\make)
  - Add the bin folder of the extracted archive to your `$PATH`.
- Use `zadig` to replace the jlink drivers with WinUSB
