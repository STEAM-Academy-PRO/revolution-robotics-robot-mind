import smbus2
import time
import pdb
import binascii
import struct
import sys

debug_logs = False
I2C_REVVY_ADDRESS = 0x2d
I2C_BOOTLOADER_ADDRESS = 0x2b

CMD_PING = 0
CMD_READ_HW = 1
CMD_RUN_BOOTLOADER = 2
CMD_UPDATE_INIT = 3
CMD_UPDATE_WRITE = 4
CMD_UPDATE = 5
CMD_GET_OP = 6
CMD_GET_APP_CRC = 7
CMD_RUN_APP = 8

crc7_table = (
  0x00, 0x09, 0x12, 0x1b, 0x24, 0x2d, 0x36, 0x3f,
  0x48, 0x41, 0x5a, 0x53, 0x6c, 0x65, 0x7e, 0x77,
  0x19, 0x10, 0x0b, 0x02, 0x3d, 0x34, 0x2f, 0x26,
  0x51, 0x58, 0x43, 0x4a, 0x75, 0x7c, 0x67, 0x6e,
  0x32, 0x3b, 0x20, 0x29, 0x16, 0x1f, 0x04, 0x0d,
  0x7a, 0x73, 0x68, 0x61, 0x5e, 0x57, 0x4c, 0x45,
  0x2b, 0x22, 0x39, 0x30, 0x0f, 0x06, 0x1d, 0x14,
  0x63, 0x6a, 0x71, 0x78, 0x47, 0x4e, 0x55, 0x5c,
  0x64, 0x6d, 0x76, 0x7f, 0x40, 0x49, 0x52, 0x5b,
  0x2c, 0x25, 0x3e, 0x37, 0x08, 0x01, 0x1a, 0x13,
  0x7d, 0x74, 0x6f, 0x66, 0x59, 0x50, 0x4b, 0x42,
  0x35, 0x3c, 0x27, 0x2e, 0x11, 0x18, 0x03, 0x0a,
  0x56, 0x5f, 0x44, 0x4d, 0x72, 0x7b, 0x60, 0x69,
  0x1e, 0x17, 0x0c, 0x05, 0x3a, 0x33, 0x28, 0x21,
  0x4f, 0x46, 0x5d, 0x54, 0x6b, 0x62, 0x79, 0x70,
  0x07, 0x0e, 0x15, 0x1c, 0x23, 0x2a, 0x31, 0x38,
  0x41, 0x48, 0x53, 0x5a, 0x65, 0x6c, 0x77, 0x7e,
  0x09, 0x00, 0x1b, 0x12, 0x2d, 0x24, 0x3f, 0x36,
  0x58, 0x51, 0x4a, 0x43, 0x7c, 0x75, 0x6e, 0x67,
  0x10, 0x19, 0x02, 0x0b, 0x34, 0x3d, 0x26, 0x2f,
  0x73, 0x7a, 0x61, 0x68, 0x57, 0x5e, 0x45, 0x4c,
  0x3b, 0x32, 0x29, 0x20, 0x1f, 0x16, 0x0d, 0x04,
  0x6a, 0x63, 0x78, 0x71, 0x4e, 0x47, 0x5c, 0x55,
  0x22, 0x2b, 0x30, 0x39, 0x06, 0x0f, 0x14, 0x1d,
  0x25, 0x2c, 0x37, 0x3e, 0x01, 0x08, 0x13, 0x1a,
  0x6d, 0x64, 0x7f, 0x76, 0x49, 0x40, 0x5b, 0x52,
  0x3c, 0x35, 0x2e, 0x27, 0x18, 0x11, 0x0a, 0x03,
  0x74, 0x7d, 0x66, 0x6f, 0x50, 0x59, 0x42, 0x4b,
  0x17, 0x1e, 0x05, 0x0c, 0x33, 0x3a, 0x21, 0x28,
  0x5f, 0x56, 0x4d, 0x44, 0x7b, 0x72, 0x69, 0x60,
  0x0e, 0x07, 0x1c, 0x15, 0x2a, 0x23, 0x38, 0x31,
  0x46, 0x4f, 0x54, 0x5d, 0x62, 0x6b, 0x70, 0x79)


SLOT_GYRO = 11
SLOT_SENSOR_1 = 6
SLOT_SENSOR_2 = 7
SLOT_SENSOR_3 = 8
SLOT_SENSOR_4 = 9

I2C_CMD_OP_START = 0
I2C_CMD_OP_GET_RESULT = 2

I2C_CMD_CMD_PING = 0
I2C_CMD_CMD_READ_HW_VER = 1
I2C_CMD_CMD_READ_FW_VER = 2
I2C_CMD_CMD_SET_MASTER_STATUS = 4
I2C_CMD_CMD_GET_OPERATION_MODE = 6
I2C_CMD_CMD_READ_APP_CRC = 7
I2C_CMD_CMD_UPDATE_INIT = 8
I2C_CMD_CMD_UPDATE_WRITE_CHUNK = 9
I2C_CMD_CMD_RUN_APP = 0x0a
I2C_CMD_CMD_RUN_BOOTLOADER = 0x0b
I2C_CMD_CMD_GET_PORT_TYPES = 0x21
I2C_CMD_CMD_SET_PORT_TYPE = 0x22
I2C_CMD_CMD_SLOT_RESET = 0x3a
I2C_CMD_CMD_SLOT_CTRL = 0x3b
I2C_CMD_CMD_READ_SLOTS = 0x3c

I2C_CMD_RSP_HEADER_SIZE = 5
I2C_CMD_RSP_PAYLOAD_OFF = 5


def log_debug(msg):
  if debug_logs:
    print(msg)

def crc7(data, crc=0xff):
  """
  >>> crc7(b'foobar')
  16
  """
  for b in data:
    crc = crc7_table[b ^ ((crc << 1) & 0xff)]
  return crc


def bytes_to_dump_str(b):
  bytestring = ' '.join(['{:02x}'.format(i) for i in b])
  return '[{}]'.format(bytestring)


class WrongHeaderCrcException(Exception):
  pass


class WrongPayloadLengthException(Exception):
  pass


class WrongPayloadCrcException(Exception):
  pass


class I2CResponse:
  # uint8_t comm_status
  # uint8_t payload_length
  # uint16_t payload_checksum
  # uint8_t header_checksum
  # uint8_t payload

  def __init__(self, data):
    header = data[0:4]
    status, payload_len, payload_crc, header_crc = struct.unpack('<BBHB', data[:I2C_CMD_RSP_PAYLOAD_OFF])
    actual_crc = crc7(header)
    if actual_crc != header_crc:
      print("Wrong CRC {}/{}: {}".format(actual_crc, header_crc, bytes_to_dump_str(data)))
      raise WrongHeaderCrcException()

#    if status > 10:
#      if status in [0x80, 0x81]:
#        status = 0
#        payload_len = 0
#
#      print(bytes_to_dump_str(data))

    self.__status = status
    self.__payload_len = payload_len
    self.__payload = b''
    payload = data[I2C_CMD_RSP_PAYLOAD_OFF:]

    if payload_len and len(payload):
      if len(payload) != payload_len:
        print('Wrong payload length, should be {}, actual: {}'.format(payload_len, len(payload)))
        raise WrongPayloadLengthException()

      actual_payload_crc = binascii.crc_hqx(payload, 0xFFFF)
      if actual_payload_crc != payload_crc:
        print('Wrong payload crc')
        raise WrongPayloadCrcException()
      self.__payload = payload

    log_debug('RSP:{} {} len:{}/{},pcrc:{:04x}({:04x})'.format(
      bytes_to_dump_str(data),
      i2c_cmd_status_to_str(status),
      len(data), payload_len,
      payload_crc, actual_crc))

  @property
  def status(self):
    return self.__status

  @property
  def payload_len(self):
    return self.__payload_len

  @property
  def payload(self):
    return self.__payload


def i2c_cmd_op_to_str(op):
  return {
    0: 'START',
    1: 'RESTART',
    2: 'GET_RESULT',
    3: 'CANCEL',
  }[op]


def i2c_cmd_cmd_to_str(cmd):
  return {
    I2C_CMD_CMD_PING: 'PING',
    I2C_CMD_CMD_READ_HW_VER: 'READ_HW_VER',
    I2C_CMD_CMD_READ_FW_VER: 'READ_FW_VER',
    I2C_CMD_CMD_SET_MASTER_STATUS: 'SET_MASTER_STA',
    I2C_CMD_CMD_GET_OPERATION_MODE: 'I2C_CMD_CMD_GET_OPERATION_MODE',
    I2C_CMD_CMD_READ_APP_CRC: 'I2C_CMD_CMD_READ_APP_CRC',
    I2C_CMD_CMD_GET_PORT_TYPES: 'GET_PORT_TYPES',
    I2C_CMD_CMD_RUN_APP: 'I2C_CMD_CMD_RUN_APP',
    I2C_CMD_CMD_RUN_BOOTLOADER: 'I2C_CMD_CMD_RUN_BOOTLOADER',
    I2C_CMD_CMD_UPDATE_INIT: 'I2C_CMD_CMD_UPDATE_INIT',
    I2C_CMD_CMD_UPDATE_WRITE_CHUNK: 'I2C_CMD_CMD_UPDATE_WRITE_CHUNK',
    I2C_CMD_CMD_SET_PORT_TYPE: 'SET_PORT_TYPE',
    I2C_CMD_CMD_SLOT_RESET: 'I2C_CMD_CMD_SLOT_RESET',
    I2C_CMD_CMD_SLOT_CTRL: 'SLOT_CTRL',
    I2C_CMD_CMD_READ_SLOTS: 'READ_SLOTS'
  }[cmd]

I2C_CMD_STATUS_OK = 0
I2C_CMD_STATUS_BUSY = 1
I2C_CMD_STATUS_PENDING = 2

def i2c_cmd_status_to_str(sta):
  status_strings = [
    "OK",
    "BUSY",
    "PENDING",
    "ERR_UNKNOWN_OP",
    "ERR_INVALID_OP",
    "ERR_CMD_INTEGRITY",
    "ERR_PAYLOAD_INTEGRITY",
    "ERR_PAYLOAD_LENGTH",
    "ERR_UNKNOWN_CMD",
    "ERR_COMMAND",
    "ERR_INTERNAL"
  ]

  if sta >= len(status_strings):
    print('<{}>'.format(sta))
    raise Exception()
  return status_strings[sta]

class I2CCommand:
  # Command header + payload:
  # uint8_t op;
  # uint8_t cmd;
  # uint8_t payload_length;
  # uint16_t payload_checksum;
  # uint8_t header_checksum;
  # uint8_t payload[0];

  def __init__(self, op, cmd, payload):
    packet_size = len(payload) + 6
    packet = bytearray(packet_size)

    cmd = cmd.to_bytes(1, 'little')
    if payload:
      packet[6:] = payload
      payload_checksum = binascii.crc_hqx(packet[6:], 0xffff)
      # get bytes of unsigned short
      high_byte, low_byte = divmod(payload_checksum, 256)
    else:
      high_byte = low_byte = 0xff

    packet[0] = op
    packet[1] = cmd[0]
    packet[2] = len(payload)
    packet[3] = low_byte
    packet[4] = high_byte
    packet[5] = crc7(packet[0:5])

    self.__p = packet

    log_debug('CMD:{} {}, cmd:{}:{: <10}'.format(
      bytes_to_dump_str(packet),
      i2c_cmd_op_to_str(op),
      i2c_cmd_cmd_to_str(cmd[0]),
      len(self.__p)))

  def get_bytes(self):
    return self.__p


class I2CBus:
  # Encapsulate smbus2 procedures for i2c read and write
  def __init__(self, bus_index, i2c_device_address):
    self.__bus = smbus2.SMBus(bus_index)
    self.__address = i2c_device_address

  def write(self, data):
    msg = smbus2.i2c_msg.write(self.__address, data)
    self.__bus.i2c_rdwr(msg)

  def read(self, num_bytes):
    # print('I2CBus::read {}'.format(num_bytes))
    msg = smbus2.i2c_msg.read(self.__address, num_bytes)
    self.__bus.i2c_rdwr(msg)
    return msg.buf[:msg.len]


class I2CTransport:
  def __init__(self, bus_index, i2c_device_address):
    self.__bus = I2CBus(bus_index, i2c_device_address)

  def __read_response(self, payload_len):
    num_retries = 5
    for i in range(num_retries):
      response_data = self.__bus.read(I2C_CMD_RSP_HEADER_SIZE + payload_len)
      try:
        return I2CResponse(response_data)
      except WrongHeaderCrcException:
        pass
      except WrongPayloadLengthException:
        pass
      except WrongPayloadCrcException:
        pass
      time.sleep(0.1)

  def __read_response_wrapper(self, payload_len, expect_response):
    while True:
      try:
        response = self.__read_response(payload_len)
        if response.status != I2C_CMD_STATUS_BUSY:
          return response
      except OSError as e:
        print(f'Exception during read: {e}')
        if not expect_response:
          return None
        raise


  def __do_transfer(self, cmd, expect_response):
    # 1. First Send cmd by i2c-write
    # 2. Next i2c-read response header, check status and payload length
    # 3. If all ok and payload not 0, i2c-read again full packet with payload
    self.__bus.write(cmd.get_bytes())

    response = self.__read_response_wrapper(0, expect_response)
    if not response:
      return None

    while response.status is I2C_CMD_STATUS_PENDING:
      cmd_get_result = I2CCommand(I2C_CMD_OP_GET_RESULT, cmd.get_bytes()[1], b'')
      self.__bus.write(cmd_get_result.get_bytes())
      response = self.__read_response_wrapper(0, False)

    if response.status != I2C_CMD_STATUS_OK:
      # raise Exception()
      return None

    if response.payload_len:
      response = self.__read_response_wrapper(response.payload_len, False)

    return response


  def send(self, cmd, payload, expect_response):
    log_debug('I2CTransfer::send cmd:{}, payload:{}'.format(cmd, payload))
    t_start = time.time()
    cmd_start = I2CCommand(I2C_CMD_OP_START, cmd, payload)
    result = self.__do_transfer(cmd_start, expect_response)
    t_end = time.time()
    log_debug('Execution time: {}'.format(t_end - t_start))
    return result


def port_enable(t, port_idx):
  payload = struct.pack('<BB', port_idx, 1)
  t.send(I2C_CMD_CMD_SLOT_CTRL, payload, True)
  time.sleep(0.1)


def port_reset(t):
  t.send(I2C_CMD_CMD_SLOT_RESET, b'', True)
  time.sleep(0.1)


last_payload = None
last_distance = b'\x00\x00\x00\x00'

def distance_get_one_sample(t):
  global last_distance
  response = t.send(I2C_CMD_CMD_READ_SLOTS, b'', True)
  if response and response.payload:
      last_distance = response.payload[2:]


distance = 0
gyro_x = 0
gyro_y = 0
gyro_z = 0


def slots_print():
  gyro_str= ','.join(['{: 3.03f}'.format(i) for i in [gyro_x, gyro_y, gyro_z]])
  gyro_str = 'gyro:' + gyro_str
  dist_str = '{}cm'.format(distance)
  print(gyro_str, dist_str)


def slot_function_sensor_1(data):
  global distance
  if len(data) == 4:
    distance = struct.unpack('<I', data)[0]
  else:
    distance = 0xffffffff


def slot_function_gyro(data):
  global gyro_x, gyro_y, gyro_z

  if len(data) == 12:
    gyro_x, gyro_y, gyro_z = struct.unpack('<fff', data)
  else:
    gyro_x, gyro_y, gyro_z = 0, 0, 0


slot_functions = {
  SLOT_GYRO : slot_function_gyro,
  SLOT_SENSOR_1: slot_function_sensor_1,
}

def get_one_sample(t):
  global last_payload
  log_debug('----SLOT_SAMPLING ----')
  response = t.send(I2C_CMD_CMD_READ_SLOTS, b'', True)
  p = response.payload
  # print(bytes_to_dump_str(response.payload))
  # if response and response.payload_len:
  #  last_payload = response.payload

  while len(p):
    slot_idx = p[0]
    slot_data_size = p[1]
    slot_data = p[2 : 2 + slot_data_size]
    p = p[2 + slot_data_size : ]
    if slot_idx not in slot_functions.keys():
      print('slot_index wrong:', bytes_to_dump_str(response.payload))
      continue
    slot_functions[slot_idx](slot_data)

  log_debug('----SLOT_SAMPLING END----')


def slot_status_monitor(t):
  while True:
    get_one_sample(t)
    slots_print()
    time.sleep(0.01)


def get_port_types(t):
  result = []
  response = t.send(I2C_CMD_CMD_GET_PORT_TYPES, b'', True)
  data = response.payload
  while len(data):
    idx = data[0]
    name_len = data[1]
    name = data[2:2+name_len]
    name = name.decode('utf-8')
    data = data[2+name_len:]
    result.append((idx, name))

  for idx, name in result:
      print('{}:{}'.format(idx, name))

  return result


def port_set_type(t, port_idx, port_type_idx):
  cmd_payload = struct.pack('<BB', port_idx + 1, port_type_idx)
  response = t.send(I2C_CMD_CMD_SET_PORT_TYPE, cmd_payload, True)


def port_set_type_by_name(t, port_idx, type_name):
  port_types = get_port_types(t)
  for idx, name in port_types:
    if name == type_name:
      port_type_idx = idx
      break
  port_set_type(t, port_idx, port_type_idx)


def run_bootloader(t):
  response = t.send(I2C_CMD_CMD_RUN_BOOTLOADER, b'', False)


def run_app(t):
  response = t.send(I2C_CMD_CMD_RUN_APP, b'', False)


def read_hw_version(t):
  response = t.send(I2C_CMD_CMD_READ_HW_VER, b'', True)
  p = response.payload
  hw_ver_str = p.decode('utf-8')
  print(f'hardware version: {hw_ver_str}')


def get_operation_mode(t):
  response = t.send(I2C_CMD_CMD_GET_OPERATION_MODE, b'', True)
  pl = response.payload
  if pl == b'\xbb':
    print('operation mode: BOOTLOADER (0xbb)')
  elif pl == b'\xaa':
    print('operation mode: APPLICATION (0xaa)')
  else:
    print('operation mode: UNKNOWN ({})'.format(pl[0]))


def get_app_crc(t):
  response = t.send(I2C_CMD_CMD_READ_APP_CRC, b'', True)
  if len(response.payload) != 4:
    raise Exception('Invalid response len')
  (crc,) = struct.unpack('<I', response.payload)
  print(f'application crc: 0x{crc:08x}')


def str_to_int(v):
  if v.startswith('0x'):
    return int(v, base=16)
  return int(v)


def update_init(t, size, crc):
  payload = struct.pack('<II', size, crc)
  response = t.send(I2C_CMD_CMD_UPDATE_INIT, payload, True)
  return response is not None


def update_write_one_chunk(t, chunk):
  response = t.send(I2C_CMD_CMD_UPDATE_WRITE_CHUNK, chunk, True)
  # time.sleep(0.5)
  return response is not None


def update_write_chunks(t, fname):
  with open(fname, 'rb') as f:
    while True:
      # by protocol payload length is only one byte, so we can
      # only send 0xff bytes at a time
      chunk = f.read(255)
      if not len(chunk):
        break
      if not update_write_one_chunk(t, chunk):
        return False
  return True


def update(t, fname):
  with open(fname, 'rb') as f:
    data = f.read()
    size = len(data)
    crc = binascii.crc32(data)
  if not update_init(t, size, crc):
    print('Update init failed, update not done')
    return False

  if not update_write_chunks(t, fname):
    print('Failed to write all chunks. update not done')
    return False

  run_app(t)
  return True


def parse_args():
  global debug_logs
  step_debug = False
  is_bootloader = False

  commands = {
    'readhw'    : (CMD_READ_HW, 0),
    'ping'      : (CMD_PING, 0),
    'runbl'     : (CMD_RUN_BOOTLOADER, 0),
    'getop'     : (CMD_GET_OP, 0),
    'getappcrc' : (CMD_GET_APP_CRC, 0),
    'runapp'    : (CMD_RUN_APP, 0),
    'updinit'   : (CMD_UPDATE_INIT, 2),
    'updwrite'  : (CMD_UPDATE_WRITE, 1),
    'upd'       : (CMD_UPDATE, 1)
  }

  cmd = CMD_READ_HW
  for i in range(1, len(sys.argv)):
    arg = sys.argv[i]
    print(f'next_arg {i} {arg}')
    if arg[0] == '-':
      flag = arg[1]
      print(f'flag = {flag}')
      if flag == 'b':
        is_bootloader = True
      elif flag == 'd':
        step_debug = True
      elif flag == 'v':
        debug_logs = True
    else:
      if arg in commands.keys():
        cmd, num_args = commands[arg]
        cmd_args = []
        for ai in range(num_args):
          i += 1
          cmd_args.append(sys.argv[i])
        print(cmd, cmd_args)

  return cmd, cmd_args, is_bootloader, step_debug


def main():
  cmd, cmd_args, is_bootloader, step_debug = parse_args()

  i2c_addr = I2C_BOOTLOADER_ADDRESS if is_bootloader else I2C_REVVY_ADDRESS
  print(f'i2c address: {i2c_addr:x}')
  t = I2CTransport(1, i2c_addr)
  if step_debug:
    pdb.set_trace()

  if cmd == CMD_PING:
    t.send(I2C_CMD_CMD_PING, b'', True)
  elif cmd == CMD_READ_HW:
    read_hw_version(t)
  elif cmd == CMD_RUN_APP:
    run_app(t)
  elif cmd == CMD_RUN_BOOTLOADER:
    run_bootloader(t)
  elif cmd == CMD_GET_OP:
    get_operation_mode(t)
  elif cmd == CMD_GET_APP_CRC:
    get_app_crc(t)
  elif cmd == CMD_UPDATE_INIT:
    size = str_to_int(cmd_args[0])
    crc = str_to_int(cmd_args[1])
    update_init(t, size, crc)
  elif cmd == CMD_UPDATE_WRITE:
    fname = cmd_args[0]
    update_write_chunks(t, fname)
  elif cmd == CMD_UPDATE:
    fname = cmd_args[0]
    update(t, fname)
  sys.exit()

  port_reset(t)
  port_set_type_by_name(t, 0, 'HC_SR04')
  port_enable(t, SLOT_GYRO)
  port_enable(t, SLOT_SENSOR_1)
  slot_status_monitor(t)


if __name__ == '__main__':
  main()
