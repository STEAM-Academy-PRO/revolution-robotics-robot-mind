import struct


def readUInt16LE(buffer, offset: int):
    return struct.unpack("<H", buffer[offset : offset + 2])[0]


def readUInt16BE(buffer, offset: int):
    return struct.unpack(">H", buffer[offset : offset + 2])[0]


def readUInt8(buffer, offset: int):
    return buffer[offset]


def readInt8(buffer, offset: int):
    return buffer[offset]


def writeUInt8(buffer, value: int, offset: int):
    struct.pack_into("<B", buffer, offset, value)


def writeInt8(buffer, value: int, offset: int):
    if value < 0:
        value = 256 + value
    struct.pack_into("<B", buffer, offset, value)


def writeUInt16LE(buffer, value: int, offset: int):
    struct.pack_into("<H", buffer, offset, value)


def writeUInt16BE(buffer, value: int, offset: int):
    struct.pack_into(">H", buffer, offset, value)


def copy(source_buffer, dest_buffer, offset: int):
    for i in range(0, min(len(dest_buffer) - offset, len(source_buffer))):
        dest_buffer[offset + i] = source_buffer[i]
