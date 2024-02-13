import { Accessor, Setter } from "solid-js"
import { createEmitter } from "@solid-primitives/event-bus";
import { RobotConfig } from "./Config";

const PORT = 8765

export type SocketWrapper = {
    send: (type: RobotMessage, message?: any) => void
    close: () => void
    on: (type: WSEventType, callback: WSEventCallback) => void
}

export enum WSEventType {
    onMessage = "onMessage",
    onError = 'onError',
    onOpen = 'onOpen',
    onClose = 'onClose'
}

export enum RobotMessage {
    configure = 'configure',
    control = 'control',
    startCamera = 'camera_start',
    stopCamera = 'camera_stop',
}

export type WSEventResult = string | Event | boolean | undefined
export type WSEventCallback = (e: WSEventResult) => void

export function connectSocket(ip: string): SocketWrapper {
    const emitter = createEmitter<Record<WSEventType, WSEventResult>>()

    let socket: WebSocket = new WebSocket(`ws://${ip}:${PORT}`);

    socket.onopen = function (e) {
        console.warn("[open] Connection established");
        console.warn("Sending to server");
        emitter.emit(WSEventType.onOpen, e)
    };

    socket.onmessage = function (event) {
        const data = JSON.parse(event.data)
        emitter.emit(WSEventType.onMessage, data)
    };

    socket.onclose = function (event) {
        if (event.wasClean) {
            console.warn(`[close] Connection closed cleanly, code=${event.code} reason=${event.reason}`);
        } else {
            // e.g. server process killed or network down
            // event.code is usually 1006 in this case
            console.warn('[close] Connection died');
        }
        emitter.emit(WSEventType.onClose, event.wasClean)
    };

    socket.onerror = function (e) {
        console.warn(`[error]`, e);
        emitter.emit(WSEventType.onError, e)
    };
    return {
        send: (type: RobotMessage, msg: any) => {
            if(type!== RobotMessage.control) console.log('send', type, msg)
            return socket.send(JSON.stringify({ type, body: msg }))
        },
        close: () => socket.close(),
        on: emitter.on
    }
}

export function connectToRobot(
    setConn: Setter<SocketWrapper | null>,
    setConnLoading: Setter<boolean>,
    endpoint: Accessor<string>,
    configString: Accessor<RobotConfig>,
    log: (msg: any) => void) {
    log(`Connecting to ${endpoint()}`)
    setConnLoading(true)
    const socket = connectSocket(endpoint())
    socket.on(WSEventType.onMessage, (data) => {
        switch (data.event) {
            case 'orientation_change': break
            case 'program_status_change': break
            case 'motor_change': break
            case 'battery_change': break
            case 'version_info': break
            case 'camera_started': break
            case 'camera_stopped': break
            default:
                console.warn(`[message] Data received from server: ${data.event}`, data.data);

                log(`${data.event}: ${JSON.stringify(data.data)}`)
        }
    })
    socket.on(WSEventType.onOpen, (e) => {
        log('Socket Connection Established!')
        setConn(socket)
        setConnLoading(false)
        socket.send(RobotMessage.configure, JSON.stringify(configString()))
    })
    socket.on(WSEventType.onClose, (wasClean) => {
        log(wasClean ? 'Socket Connection Closed Nicely!' : 'Socket Connection Dropped.')
        setConn(null)
        setConnLoading(false)
    })
    socket.on(WSEventType.onError, (e) => {
        console.error(e)
        if (e instanceof Error)
            log((e as Error).message)
    })
}


export function disconnect(conn: Accessor<SocketWrapper | null>, setConn: Setter<SocketWrapper | null>) {
    if (conn()) {
        conn()?.close()
        setConn(null);
    }
}