""" Unified Control Message Parser """

# Documentation of control messages here:
# https://docs.google.com/document/d/10fSZSteEr80KhezFd8z21VvdrG8Kk38ko8qecDbktcM/edit


import struct
from revvy.utils.functions import bits_to_bool_list

def parse_control_message(data):
    """ From a control message, parse out analog values, deadlines, and button values """
    analog_values = data[1:7]
    deadline_packed = data[7:11]
    next_deadline = struct.unpack('<I', deadline_packed)[0]
    button_values = bits_to_bool_list(data[11:15])

    return [analog_values, next_deadline, button_values]
