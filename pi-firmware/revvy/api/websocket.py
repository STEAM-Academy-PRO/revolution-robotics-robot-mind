""" Simple WebSocket Remote controller for robot """
import asyncio
import json
from shutil import ExecError
import struct
import threading
from revvy.robot_manager import RobotManager
import websockets

from revvy.robot.rc_message_parser import parse_control_message
from revvy.robot_config import RobotConfig

from revvy.robot.remote_controller import RemoteControllerCommand
from revvy.utils.logger import get_logger

log = get_logger('WebSocket')

SERVER_PORT=8765

log = get_logger('WS')

class RobotWebSocketApi:
    def __init__(self, robot_manager: RobotManager):
        self._robot_manager = robot_manager
        self._connections = []
        self.thread()

    def start(self):
        asyncio.set_event_loop(asyncio.new_event_loop())
        log('Starting WebSocket server')
        server = websockets.serve(self.incoming_connection, "0.0.0.0", SERVER_PORT)
        log('Started WebSocket server')
        asyncio.get_event_loop().run_until_complete(server)
        asyncio.get_event_loop().run_forever()

    def thread(self):
        websocket_thread = threading.Thread(target=self.start)
        websocket_thread.start()

    async def incoming_connection(self, websocket, path):
        try:
            # Ditch former connections!
            # self._robot_manager.set_communication_interface_callbacks(self)
            # self._connections.append(websocket)

            # Print a message when a new connection is established
            log(f"Client connected: '{path}' - {websocket.remote_address}")

            await websocket.send(json.dumps(self._robot_manager._robot.battery))

            # Listen for incoming messages
            async for message_raw in websocket:
                # log(f"Received message: {message_raw}")

                message = json.loads(message_raw)

                message_type = message["type"]

                try:
                    if message_type == 'configure':
                        log(f'Incoming Configuration Message: [{message_type}]')

                        parsed_config = RobotConfig.from_string(message["body"])
                        self._robot_manager.robot_configure(parsed_config,
                            self._robot_manager.start_remote_controller)

                    if message_type == 'control':
                        json_data = message["body"]
                        data = struct.pack('B' * len(json_data), *[json_data[str(i)] for i in range(len(json_data))])

                        [analog_values, deadline_packed, next_deadline, button_values] = parse_control_message(data)

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
                ws.send(json.dumps(message))
            except Exception as e:
                log(f'send error {str(e)}')
                log(f'{message}')

    def disconnect(self):
        """ Disconnects all clients """
        for ws in self._connections:
            ws.close()

        self._connections = []

    def update_session_id(self, id):
        self.send(['session_id', id])

    def update_orientation(self, vector_orientation):
        self.send(['orientation', vector_orientation])

    def update_gyro(self, vector_list):
        self.send(['gyro', vector_list])

    def update_motor(self, id, power, speed, pos):
        self.send(['motor', id, power, speed, pos])

    def update_sensor(self, raw_value):
        self.send(['sensor', raw_value])

    def update_script_variable(self, script_variables):
        # self.send(['script_var', script_variables])
        pass

    def update_state_control(self, control_state):
        self.send(['state', control_state])

    def update_timer(self, time):
        self.send(['timer', time])

    def update_battery(self, bat_main, charger_status, motor, motor_present):
        log('bat update')
        self.send(['battery', bat_main, charger_status, motor, motor_present])

