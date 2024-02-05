""" Simple WebSocket Remote controller for robot """
import asyncio
import json
import struct
import threading
from revvy.robot.robot_events import RobotEvent
from revvy.robot_manager import RobotManager
import websockets

from revvy.robot.rc_message_parser import parse_control_message
from revvy.robot_config import RobotConfig

from revvy.robot.remote_controller import RemoteControllerCommand
from revvy.utils.logger import get_logger

log = get_logger('WebSocket')

SERVER_PORT=8765

log = get_logger('WS')

send_control_events = [RobotEvent.BATTERY_CHANGE,
                  RobotEvent.BACKGROUND_CONTROL_STATE_CHANGE,
                  RobotEvent.ORIENTATION_CHANGE,
                  RobotEvent.SCRIPT_VARIABLE_CHANGE
                  ]

ignore_log_events = [
    RobotEvent.ORIENTATION_CHANGE,
    RobotEvent.TIMER_TICK,
    RobotEvent.MCU_TICK,
    RobotEvent.GYRO_CHANGE,
    RobotEvent.MOTOR_CHANGE
]

class RobotWebSocketApi:
    def __init__(self, robot_manager: RobotManager):
        self._robot_manager = robot_manager
        self._connections = []
        self.thread()

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
        asyncio.set_event_loop(asyncio.new_event_loop())
        log('Starting WebSocket server')
        server = websockets.serve(self.incoming_connection, "0.0.0.0", SERVER_PORT)
        log(f'Started WebSocket server on {SERVER_PORT}')
        asyncio.get_event_loop().run_until_complete(server)
        asyncio.get_event_loop().run_forever()

    def thread(self):
        websocket_thread = threading.Thread(target=self.start)
        websocket_thread.start()

    async def incoming_connection(self, websocket, path):
        try:
            # Ditch former connections!
            # self._robot_manager.set_communication_interface_callbacks(self)
            self._connections.append(websocket)

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
                ws.send(json.dumps(message))
            except Exception as e:
                log(f'send error {str(e)}')
                log(f'{message}')

    def disconnect(self):
        """ Disconnects all clients """
        for ws in self._connections:
            ws.close()

        self._connections = []
