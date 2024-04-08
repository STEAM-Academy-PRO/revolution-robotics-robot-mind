MCU status slots
================

The MCU exposes a number of status slots that are used to notify the host (Raspberry Pi) about
data/status changes in specific software components.

The system consists of a few different components:

- `McuStatusSlots` collects data from other software components, attaches version info for change
  detection and stores the data in memory.
- `McuStatusCollector` keeps track of which slot has changed since last read, manages enabling and
  disabling of individual slots and serializes data into a single buffer for the host to read.
- `CommWrapper_McuStatusCollector` implements the [I2C](i2c.md) command handlers that then interface
  to `McuStatusCollector`.

> There are some opportunities to simplify this system. `McuStatusCollector` and `McuStatusSlots`
> could/should probably be merged. `McuStatusSlots` shouldn't contain knowledge about what each
> slot contains. The version tag is prone to the ABA problem, and we should replace it with a
> boolean flag instead that signals "changed since last read" (i.e. a one element queue with
> dynamic element size - maybe as a multi-instance component that implements a single queue?).
> *Slot IDs should be project configuration*

How data flows through this mechanism:

- During initialization, software components indicate the size of the status value they wish to
  send via the status slot mechanism. The `McuStatusSlots` component makes sure a suitable buffer
  is allocated.
- Software components emit events containing a byte array with status information. The format of
  the data is specific to the source component.
- `McuStatusSlots` compares the data against what's currently in its buffer. If the data has changed
  it stores the new value in the buffer and increments the version info.
- When the host issues a read command, `McuStatusCollector` reads all enabled slots, and serializes
  the read values into a single buffer that is then returned to the host.
- The host's software parses the data and passes them to subscriber components for further
  processing.
