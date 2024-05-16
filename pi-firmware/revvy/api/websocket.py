""" Simple WebSocket Remote controller for robot """

import asyncio
from enum import Enum
import json
import struct
import threading
from time import time
import traceback
from typing import Any
from revvy.api.camera import Camera
from revvy.utils.error_reporter import RobotErrorType
from revvy.utils.version import VERSION

import websockets

from revvy.robot.robot_events import RobotEvent
from revvy.robot_manager import RobotManager


from revvy.robot.rc_message_parser import parse_control_message
from revvy.robot_config import RobotConfig

from revvy.utils.logger import LogLevel, get_logger

log = get_logger("WebSocket")

SERVER_PORT = 8765

log = get_logger("WS")

send_control_events = [
    RobotEvent.BATTERY_CHANGE,
    RobotEvent.BACKGROUND_CONTROL_STATE_CHANGE,
    RobotEvent.ORIENTATION_CHANGE,
    RobotEvent.SCRIPT_VARIABLE_CHANGE,
    RobotEvent.PROGRAM_STATUS_CHANGE,
    RobotEvent.SENSOR_VALUE_CHANGE,
    RobotEvent.CAMERA_STARTED,
    RobotEvent.CAMERA_STOPPED,
    RobotEvent.CAMERA_ERROR,
    RobotEvent.CONTROLLER_LOST,
    RobotEvent.ERROR,
]

ignore_log_events = [
    RobotEvent.ORIENTATION_CHANGE,
    RobotEvent.TIMER_TICK,
    RobotEvent.MCU_TICK,
    RobotEvent.PROGRAM_STATUS_CHANGE,
    RobotEvent.BATTERY_CHANGE,
    RobotEvent.SENSOR_VALUE_CHANGE,
]


# Function to check if an object is a named tuple
def is_namedtuple(obj) -> bool:
    return isinstance(obj, tuple) and hasattr(obj, "_fields")


class NamedTupleEncoder(json.JSONEncoder):
    def default(self, o) -> Any:
        if is_namedtuple(o):
            return o._asdict()  # Convert the named tuple to a dictionary
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, bytes):
            return str(o)
        if callable(getattr(o, "__json__", None)):
            return o.__json__()
        return super().default(o)


# Function to encode data dynamically
def encode_data(data) -> str:
    return json.dumps(data, cls=NamedTupleEncoder)


class RobotWebSocketApi:
    def __init__(self, robot_manager: RobotManager):
        self._robot_manager = robot_manager
        self._connections = []
        self.thread()
        self._event_loop = None

        # Loosely connected module, so I do not write the camera
        # into the robot manager, as it's not currently used in prod.
        # Sends events through robot state!
        self._camera = Camera(robot_manager._robot_state.trigger)

        robot_manager.on_all(self.all_event_capture)

    def all_event_capture(self, object_ref, evt, data=None) -> None:
        if evt not in ignore_log_events:
            log(f"{evt} {str(data)}")
        if evt in send_control_events:
            self.send({"event": evt, "data": data})

    def start(self) -> None:
        """Starts separate thread"""
        asyncio.set_event_loop(asyncio.new_event_loop())
        log("Starting WebSocket server")
        server = websockets.serve(self.incoming_connection, "0.0.0.0", SERVER_PORT)
        log(f"Started WebSocket server on {SERVER_PORT}")
        self._event_loop = asyncio.get_event_loop()
        self._event_loop.run_until_complete(server)
        self._event_loop.run_forever()

    def thread(self) -> None:
        websocket_thread = threading.Thread(target=self.start, name="WebSocket")
        websocket_thread.start()

    async def incoming_connection(self, websocket, path) -> None:
        """On new connection, a new this will be ran."""
        try:
            # Ditch former connections!
            # self._robot_manager.set_communication_interface_callbacks(self)
            self._connections.append(websocket)

            # Print a message when a new connection is established
            log(f"Client connected: '{path}' - {websocket.remote_address}")

            # Initial state sends.
            self.send(
                {"event": RobotEvent.BATTERY_CHANGE, "data": self._robot_manager.robot.battery}
            )

            self._robot_manager.robot.play_tune("s_connect")

            self.send({"event": "version_info", "data": VERSION.get()})
            last_control_message = time()
            # Listen for incoming messages
            async for message_raw in websocket:
                # log(f"Received message: {message_raw}")

                message = json.loads(message_raw)

                message_type = message["type"]

                try:
                    if message_type == "camera_start":
                        self._camera.start()

                    if message_type == "camera_stop":
                        self._camera.stop()

                    if message_type == "configure":
                        log(f"Incoming Configuration Message: [{message_type}]")

                        parsed_config = RobotConfig.from_string(message["body"])
                        configure_start_time = time()
                        self._robot_manager.robot_configure(parsed_config)
                        self.send(
                            {"event": "confirm_success", "data": time() - configure_start_time}
                        )

                    if message_type == "control":
                        json_data = message["body"]
                        data = bytearray(
                            struct.pack(
                                "B" * len(json_data),
                                *[json_data[str(i)] for i in range(len(json_data))],
                            )
                        )

                        command = parse_control_message(data)
                        # log(
                        #     f"Control message: {command.analog} - {round(time() - last_control_message, 4)*1000}ms"
                        # )
                        last_control_message = time()
                        self._robot_manager.handle_periodic_control_message(command)
                        # Send back the packet ID to see LAG.
                        self.send({"event": "control_confirm", "data": json_data["0"]})
                except Exception as e:
                    log(f"Loop failed: {message_type}: {e}")
                    stack = traceback.format_exc()
                    self.send(
                        {
                            "event": "error",
                            "data": {
                                "stack": f"{stack}\n{message_type}: {e}",
                                "type": RobotErrorType.SYSTEM,
                                "ref": 0,
                            },
                        }
                    )

        except websockets.exceptions.ConnectionClosedError:
            pass  # Connection closed, ignore the error
            self._robot_manager.robot.play_tune("s_disconnect")
        finally:
            # Print a message when a connection is closed
            log(f"Client disconnected: {websocket.remote_address}")

    def send(self, message) -> None:
        assert self._event_loop is not None

        for ws in self._connections:
            try:
                # log(f'msg: {message["event"]}')
                asyncio.run_coroutine_threadsafe(ws.send(encode_data(message)), self._event_loop)
            except Exception as e:
                log(f"send error {str(e)}", LogLevel.ERROR)
                print(message)
                log(f"{message}")

    def disconnect(self) -> None:
        """Disconnects all clients"""
        for ws in self._connections:
            ws.close()

        self._connections = []
