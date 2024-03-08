I2C communication protocol
==========================

Addresses
---------

The MCU implements the same protocol for the bootloader and the application. The physical interface
is I2C. The different operation modes use different I2C addresses:

- Bootloader: `0x2B`
- Application: `0x2D`

Protocol overview
-----------------

The MCU implements a request-response protocol. The Pi firmware acts as the `dom` issuing requests,
the MCU acts as a `sub` processing the requests and providing responses. For each `dom` request the
`sub` sends a response. In terms of I2C, this means that the `dom` writes to the `sub`'s address,
then reads from that address repeatedly until a response is returned. This protocol is then used
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

A `StartCommand` must be polled for a result. This polling should be repeated until a non-`Pending`
result is returned. If a command of the same kind is already being executed when sending
`StartCommand`, an `InvalidOperation` error is returned.

### GetResult Request

Polls a Command and returns its result if it's finished. Request contains which Command should be
polled. Returns `Pending` as status while the command execution is not finished.

A `GetResult` must be preceded by a `StartCommand`. If command execution is not in progress, an
`InvalidOperation` error is returned.

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

- `0, Comm_Status_Ok`:
  Operation executed successfully, response may contain payload. This status has different meanings
  depending on the Request:
  - `StartCommand`: the command was executed and its result is immediately available.
  - `GetResult`: the command has finished its execution and its result is available.
- `1, Comm_Status_Busy`: the previous command has not been fully processed yet. The `dom` should repeat reading the response.
- `2, Comm_Status_Pending`: command execution is in progress, no data supplied. The `dom` should continue polling using the `GetResult` request.
- `3, Comm_Status_Error_UnknownOperation`: the `Request` field contains an invalid value
- `4, Comm_Status_Error_InvalidOperation`: in case Pi sends a `GetResult` but the MCU does not implement it for the particular command.
- `5, Comm_Status_Error_CommandIntegrityError`: The Request's header was received with a CRC error.
- `6, Comm_Status_Error_PayloadIntegrityError`: The Request's payload was received with a CRC error.
- `7, Comm_Status_Error_PayloadLengthError`: The Request's payload length does not match the `Payload Length` field.
- `8, Comm_Status_Error_UnknownCommand`: The `RPC ID` contains an unexpected value.
- `9, Comm_Status_Error_CommandError`: response contains additional command-specific error data
- `10, Comm_Status_Error_InternalError`: other errors indicating internal programming errors

> FIXME: `Comm_Status_Error_PayloadLengthError` is also used in the command implementations and can
> signal that the payload is not of an expected length. While technically not incorrect, should
> return separate errors.