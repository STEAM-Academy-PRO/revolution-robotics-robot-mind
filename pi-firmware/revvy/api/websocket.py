""" Simple WebSocket Remote controller for robot """
import asyncio
from enum import Enum
import json
import struct
import threading
from revvy.utils.version import VERSION

import websockets

from revvy.robot.robot_events import RobotEvent
from revvy.robot_manager import RobotManager


from revvy.robot.rc_message_parser import parse_control_message
from revvy.robot_config import RobotConfig

from revvy.robot.remote_controller import RemoteControllerCommand
from revvy.utils.logger import LogLevel, get_logger

log = get_logger('WebSocket')

SERVER_PORT=8765

log = get_logger('WS')

send_control_events = [RobotEvent.BATTERY_CHANGE,
                  RobotEvent.BACKGROUND_CONTROL_STATE_CHANGE,
                  RobotEvent.ORIENTATION_CHANGE,
                  RobotEvent.SCRIPT_VARIABLE_CHANGE,
                  RobotEvent.PROGRAM_STATUS_CHANGE,
                  RobotEvent.MOTOR_CHANGE,
                  RobotEvent.SENSOR_VALUE_CHANGE
                  ]

ignore_log_events = [
    RobotEvent.ORIENTATION_CHANGE,
    RobotEvent.TIMER_TICK,
    RobotEvent.MCU_TICK,
    RobotEvent.MOTOR_CHANGE,
    RobotEvent.PROGRAM_STATUS_CHANGE
]



# Function to check if an object is a named tuple
def is_namedtuple(obj):
    return isinstance(obj, tuple) and hasattr(obj, '_fields')

class NamedTupleEncoder(json.JSONEncoder):
    def default(self, obj):
        if is_namedtuple(obj):
            return obj._asdict()  # Convert the named tuple to a dictionary
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)

# Function to encode data dynamically
def encode_data(data):
    return json.dumps(data, cls=NamedTupleEncoder)



class RobotWebSocketApi:
    def __init__(self, robot_manager: RobotManager):
        self._robot_manager = robot_manager
        self._connections = []
        self.thread()
        self._event_loop = None

        robot_manager.on("all", self.all_event_capture)

    def all_event_capture(self, object_ref, evt, data=None):
        if evt not in ignore_log_events:
            log(f'{evt} {str(data)}')
        if evt in send_control_events:
            self.send({
                "event": evt,
                "data": data
            })

    def start(self):
        """ Starts separate thread """
        asyncio.set_event_loop(asyncio.new_event_loop())
        log('Starting WebSocket server')
        server = websockets.serve(self.incoming_connection, "0.0.0.0", SERVER_PORT)
        log(f'Started WebSocket server on {SERVER_PORT}')
        self._event_loop = asyncio.get_event_loop()
        self._event_loop.run_until_complete(server)
        self._event_loop.run_forever()

    def thread(self):
        websocket_thread = threading.Thread(target=self.start)
        websocket_thread.start()

    async def incoming_connection(self, websocket, path):
        """ On new connection, a new this will be ran. """
        try:
            # Ditch former connections!
            # self._robot_manager.set_communication_interface_callbacks(self)
            self._connections.append(websocket)

            # Print a message when a new connection is established
            log(f"Client connected: '{path}' - {websocket.remote_address}")

            # Initial state sends.
            self.send({
                "event": RobotEvent.BATTERY_CHANGE,
                "data": self._robot_manager.robot.battery
            })

            self.send({
                "event": "version_info",
                "data": VERSION.get()
            })

            # Listen for incoming messages
            async for message_raw in websocket:
                # log(f"Received message: {message_raw}")

                message = json.loads(message_raw)

                message_type = message["type"]

                try:
                    if message_type == 'configure':
                        log(f'Incoming Configuration Message: [{message_type}]')

                        parsed_config = RobotConfig.from_string(message["body"])
                        self._robot_manager.robot_configure(parsed_config)

                    if message_type == 'control':
                        json_data = message["body"]
                        data = struct.pack('B' * len(json_data), *[json_data[str(i)] for i in range(len(json_data))])

                        [analog_values, next_deadline, button_values] = parse_control_message(data)

                        message_handler = self._robot_manager.handle_periodic_control_message

                        if message_handler:
                            message_handler(RemoteControllerCommand(analog=analog_values,
                                                        buttons=button_values,
                                                        background_command=None,
                                                        next_deadline=next_deadline))
                except Exception as e:
                    log(f'Control message failed: {message_type}: {e}')
                # Send the received message back to the client
                # await websocket.send(f"Received: {message_raw}")

        except websockets.exceptions.ConnectionClosedError:
            pass  # Connection closed, ignore the error
        finally:
            # Print a message when a connection is closed
            log(f"Client disconnected: {websocket.remote_address}")


    def send(self, message):
        for ws in self._connections:
            try:
                asyncio.run_coroutine_threadsafe(ws.send(encode_data(message)), self._event_loop)
            except Exception as e:
                log(f'send error {str(e)}', LogLevel.ERROR)
                print (message)
                log(f'{message}')

    def disconnect(self):
        """ Disconnects all clients """
        for ws in self._connections:
            ws.close()

        self._connections = []

