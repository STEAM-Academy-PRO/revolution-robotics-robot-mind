import { RobotMessage, SocketWrapper } from "./Communicator"

export function uploadConfig(conn: SocketWrapper|null, config: any){
    conn?.send(RobotMessage.configure, JSON.stringify(config))
}
