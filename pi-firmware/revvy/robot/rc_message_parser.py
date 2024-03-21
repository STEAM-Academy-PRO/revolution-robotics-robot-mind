""" Unified Control Message Parser """

# Documentation of control messages here:
# https://docs.google.com/document/d/10fSZSteEr80KhezFd8z21VvdrG8Kk38ko8qecDbktcM/edit


from revvy.robot.remote_controller import BleAutonomousCmd, RemoteControllerCommand
from revvy.utils.functions import bits_to_bool_list


def parse_control_message(data: bytearray) -> RemoteControllerCommand:
    """From a control message, parse out analog values, deadlines, and button values"""
    analog_values = data[1:7]
    deadline_packed = data[7:11]
    next_deadline = int.from_bytes(deadline_packed, byteorder="little")
    button_values = bits_to_bool_list(data[11:15])

    return RemoteControllerCommand(
        analog=analog_values,
        buttons=button_values,
        background_command=BleAutonomousCmd.NONE,
        next_deadline=next_deadline,
    )
