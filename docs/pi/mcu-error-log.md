Reading the MCU error log
-------------------------

The MCU records certain errors. Pi firmware contains tools to read these error records. To do this,
`ssh` into the brain, then navigate to the most recent installed package (e.g. `RevvyFramework/user/packages/revvy-0.1.1298/`). The following commands are now available:

- `python -m tools.read_errors`: Reads the error log from the MCU.
- `python -m tools.read_errors --inject-test-error`: Records a test error, then reads the error log.
- `python -m tools.read_errors --clear`: Reads the error log and then deletes it from the MCU.
