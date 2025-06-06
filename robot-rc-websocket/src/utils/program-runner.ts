// We have to send the control messages whenever we uploaded it, or else it resets configuration state.
// Try uncommenting the lines with doSendMove in them. The first time it stops receiving the messages
// on the robot the state resets to not configured.

import { RobotConfigV1 } from "./Config";
import { RobotMessage, SocketWrapper, WSEventResult, WSEventType } from "./Communicator";
import { uploadConfig } from "./commands";

export class RRController {
  i = 0;

  isActive = false;
  isConnected = false;
  conn: SocketWrapper;
  config: RobotConfigV1;
  subscription: any;

  constructor(connection: SocketWrapper, configuration: RobotConfigV1) {
    this.conn = connection;
    this.config = configuration
    this.i = 0;
  }

  async start(pythonCode: string) {
    const config = this.getConfig(this.config, pythonCode);
    await uploadConfig(this.conn, this.config);
    this.isConnected = true;
    this.subscription = this.conn.on(WSEventType.onMessage, (e: WSEventResult) => {
      if (typeof e !== "object" || !("event" in e)) {
        console.error("[message] Invalid message received from server:", e);
        return;
      }
      switch (e?.event) {
        case "confirm_success":
          this.sendControlMessage();
          break;
        case "control_confirm":
          // Small delay to have at least 15 ms between messages.
          setTimeout(() => this.sendControlMessage(), 10);
          break;
        case "orientation_change":
          break;
        case "battery_change":
          break;
        case "version_info":
          break;
        case "program_status_change":
          break;
        case "controller_lost":
          break;
        case "sensor_value_change":
          break;
        case "error":
          break;
        default:
          console.log(`[message] Data received from server: ${e.event}`);
      }
    });

  }

  getConfig(config: RobotConfigV1, pythonCode: string): RobotConfigV1 {
    return Object.assign({}, config, {
      blocklyList: {
        pythonCode: btoa(pythonCode),
        assignments: {
          background: 0
        }
      }
    });
  }

  sendControlMessage() {
    if (!this.isActive || !this.isConnected) {
      return;
    }

    const controlMessageId = this.i++ % 127; // keepalive - no need to change this as it's bluetooth specific

    const ctrlArray = new Uint8Array([
      controlMessageId,
      127, // UInt8, left-right analog, value range: 0-255
      127, // UInt8, bottom-top analog, value range: 0-255

      127, // UInt8, left-right analog, value range: 0-255
      127, // UInt8, bottom-top analog, value range: 0-255
      0, // unused analog
      0, // unused analog

      0, // Reserved
      0, // Reserved
      0, // Reserved
      0, // Reserved

      0, // UInt8, button group 1, 1 button per bit
      0, // UInt8, button group 2, 1 button per bit
      0, // UInt8, button group 3, 1 button per bit
      0, // UInt8, button group 4, 1 button per bit
    ]);

    this.isActive && this.conn?.send(RobotMessage.control, ctrlArray);
  }
}
