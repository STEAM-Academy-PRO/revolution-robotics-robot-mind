I2C communication protocol
==========================

Addresses
---------

The MCU implements the same protocol for the bootloader and the application. The different operation
modes use different I2C addresses:

- Bootloader: `0x2B`
- Application: `0x2D`

Protocol overview
-----------------

The MCU implements a request-response protocol. The Pi firmware acts as the `dom` issuing requests,
the MCU acts as a `sub` processing the requests and providing responses. This protocol is then used
to define higher level commands.

Commands are firmware procedures that may run for an arbitrarily long time. Multiple different
commands may run at the same time.

> Currently, we only start one command at a time in the Pi firmware.

### Format of a request

Requests control the Command execution. The MCU may implement custom Command-specific handling for
each request kind. The MCU responds to unknown Request values with an `UnknownOperation` error as
the `Status`. The dom may issue the following requests:

### StartCommand Request

Starts a Command. May contain a Command-specific payload.
May immediately call the `GetResult` handler and provide the result.

### GetResult Request

Polls a Command and returns its result if it's finished.
Request contains which Command should be polled.
Returns `Pending` as status while the command execution is not finished.

### CancelCommand Request

Calls the Cancel handler and returns its response. May be unimplemented.

### RestartCommand Request

Shorthand that Cancels and Starts the command again. May contain a Command-specific payload.

> Cancel and Restart are not used currently by the Pi firmware. Maybe we should implement a
> max run time for each command and send a Cancel on timeout, but the MCU could only log the
> cancellation and reset itself in most cases.

```
Request
+--------+---------+
| Header | Payload |
+--------+---------+

Header
+------------------+-----------------+-------------------------+---------------------+-------------+
| Request (1 byte) | RPC ID (1 byte) | Payload length (1 byte) | Payload CRC (CRC16) | Header CRC7 |
+------------------+-----------------+-------------------------+---------------------+-------------+
```

Each Request may contain at most 255 bytes of payload. Interpretation of this payload is
Command-specific. If a write transaction is longer than the header plus the indicated payload
length, an `InternalError` is returned as the `Status`.

> FIXME: ^this is what we should do. Currently we ignore extra bytes as long as they fit in the
> buffer.

### Format of a response

```
Response
+--------+---------+
| Header | Payload |
+--------+---------+

Header
+-----------------+-------------------------+---------------------+-------------+
| Status (1 byte) | Payload length (1 byte) | Payload CRC (CRC16) | Header CRC7 |
+-----------------+-------------------------+---------------------+-------------+
```

Possible status values:

```c
typedef enum
{
    Comm_Status_Ok,      /* operation executed successfully, response may contain payload */
    Comm_Status_Busy,    /* command handler is not ready with a response yet */
    Comm_Status_Pending, /* command execution is in progress, no data supplied */

    Comm_Status_Error_UnknownOperation,
    Comm_Status_Error_InvalidOperation, /* in case GetResult is used but no command is pending */
    Comm_Status_Error_CommandIntegrityError,
    Comm_Status_Error_PayloadIntegrityError,
    Comm_Status_Error_PayloadLengthError, /* data lost because message was too long */
    Comm_Status_Error_UnknownCommand,
    Comm_Status_Error_CommandError, /* response contains additional command-specific error data */
    Comm_Status_Error_InternalError /* other errors indicating internal programming errors */
} Comm_Status_t;
```

> TODO: What's the difference between Busy and Pending? What if I send a Get Result without
> a prior Start?
