import { Accessor, createSignal } from "solid-js"
import { createEmitter } from "@solid-primitives/event-bus";

const PORT = 8765

export type SocketWrapper = {
    send: (type: RobotMessage, message: any) => void
    close: () => void
    on: (type: WSEventType, callback: WSEventCallback) => void
}

export enum WSEventType {
    onMessage = "onMessage",
    onError = 'onError',
    onOpen = 'onOpen',
    onClose = 'onClose'}

export enum RobotMessage {
    configure = 'configure',
    control = 'control'
}

export type WSEventResult = string|Event|boolean|undefined
export type WSEventCallback = (e: WSEventResult) => void

export function connectToRobot(ip: string): SocketWrapper {
    const emitter = createEmitter<Record<WSEventType, WSEventResult>>()

    let socket: WebSocket = new WebSocket(`ws://${ip}:${PORT}`);

    socket.onopen = function (e) {
        console.warn("[open] Connection established");
        console.warn("Sending to server");
        emitter.emit(WSEventType.onOpen, e)
    };

    socket.onmessage = function (event) {
        console.warn(`[message] Data received from server: ${event.data}`);
        emitter.emit(WSEventType.onMessage, event.data)
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
        send: (type: RobotMessage, msg: any) =>
            socket.send(JSON.stringify({type, body: msg})),
        close: () => socket.close(),
        on: emitter.on
    }
}