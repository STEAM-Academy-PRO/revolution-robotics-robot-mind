import { RobotMessage, SocketWrapper } from "./Communicator"
import { RobotConfigV1 } from "./Config"

export function uploadConfig(conn: SocketWrapper | null, config: RobotConfigV1) {
    conn?.send(RobotMessage.configure, JSON.stringify(config))
}
