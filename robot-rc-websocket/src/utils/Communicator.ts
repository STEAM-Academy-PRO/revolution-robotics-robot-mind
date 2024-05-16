import { createSignal } from "solid-js"
import { createEmitter } from "@solid-primitives/event-bus";
import { currentConfig } from "./Config";
import { LogLevel, log } from "./log";
import { RobotError } from "./Types";
import { conn, endpoint, setConn } from "../settings";

const PORT = 8765

export const [connLoading, setConnLoading] = createSignal<boolean>(false)

export function connectOrDisconnect() {
    if (conn()) {
        disconnect()
    } else {
        connectToRobot()
    }
}

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
        console.error(`[error]`, e);
        emitter.emit(WSEventType.onError, e)
    };
    return {
        send: (type: RobotMessage, msg: any) => {
            if (type !== RobotMessage.control) {
                console.warn('send', type, msg)
            }
            return socket.send(JSON.stringify({ type, body: msg }))
        },
        close: () => socket.close(),
        on: emitter.on
    }
}

export function connectToRobot() {

    if (!endpoint()) {
        log('Please enter an IP address to connect to your robot!')
        throw new Error('Missing IP address!')
    }
    log(`Connecting to ${endpoint()}`)
    setConnLoading(true)
    const socket = connectSocket(endpoint())
    socket.on(WSEventType.onMessage, (data) => {
        switch (data.event) {
            case 'orientation_change': break
            case 'program_status_change': break
            case 'battery_change': break
            case 'version_info': break
            case 'camera_started': break
            case 'camera_stopped': break
            case 'sensor_value_change': break
            case 'control_confirm': break
            case 'error':
                let type = ''
                switch (data.data.type) {
                    case RobotError.BLOCKLY_BACKGROUND: type = 'Blockly Background'; break;
                    case RobotError.BLOCKLY_BUTTON: type = 'Blockly Button'; break;
                    case RobotError.MCU: type = 'MCU'; break;
                    case RobotError.SYSTEM: type = 'System'; break;
                }

                const stack = data.data.stack.trim().split('\n')
                const message = stack.pop()
                log(`[error] ${type}: ${data.data.ref}:`, LogLevel.ERROR)
                log(stack.join('\n'), LogLevel.WARN)
                log(message, LogLevel.ERROR)
                break
            default:
                console.warn(`[message] Data received from server: ${data.event}`, data.data);

                log(`${data.event}: ${JSON.stringify(data.data)}`)
        }
    })
    socket.on(WSEventType.onOpen, (e) => {
        log('Socket Connection Established!')
        setConn(socket)
        setConnLoading(false)
        socket.send(RobotMessage.configure, JSON.stringify(currentConfig()))
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


export function disconnect() {
    if (conn()) {
        conn()?.close()
        setConn(null);
    }
}