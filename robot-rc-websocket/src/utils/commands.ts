import { RobotMessage, SocketWrapper } from "./Communicator"
import { RobotConfig } from "./Config"

export function uploadConfig(conn: SocketWrapper|null, config: RobotConfig){
    conn?.send(RobotMessage.configure, JSON.stringify(config))
}
