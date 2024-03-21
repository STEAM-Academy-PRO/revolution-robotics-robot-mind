import { Accessor, Show, createMemo, createSignal } from "solid-js"
import { RobotMessage, WSEventType } from "../utils/Communicator"
import styles from './Play.module.css'
import { conn, endpoint } from "../settings"


enum CameraState {
    offline = 'offline',
    connecting = 'connecting',
    connected = 'connected',
}

let state = CameraState.connected

function CameraController(): {
    state: Accessor<CameraState>,
    connect: () => void,
    disconnect: () => void
} {
    const [state, setState] = createSignal(CameraState.offline);
    return {
        state,
        connect() {
            const connection = conn()
            if (connection) {
                setState(CameraState.connecting)
                connection.send(RobotMessage.startCamera)
                connection.on(WSEventType.onMessage, (data) => {
                    if (data.event === 'camera_started') {
                        setState(CameraState.connected)
                    }
                    if (data.event === 'camera_stopped') {
                        setState(CameraState.offline)
                    }
                })
            }
        },
        disconnect() {
            const connection = conn()
            if (connection) {
                connection.send(RobotMessage.stopCamera)
                setState(CameraState.offline)
            }
        }

    }
}

export function CameraView() {
    const controller = CameraController()

    const cameraAddress = createMemo(() =>
        conn() ? `http://${endpoint()}:8080/?action=stream` : ''
    )

    return <>
        <div class={styles.cameraButtonWrapper}>
            <Show when={controller.state() === CameraState.offline && conn()}>
                <button class={styles.cameraOn} onClick={controller.connect}>Camera ON</button>
            </Show>
            <Show when={controller.state() === CameraState.connected}>
                <button class={styles.cameraOff} onClick={controller.disconnect}>Camera OFF</button>
            </Show>
            <Show when={controller.state() === CameraState.connecting}>
                <button disabled>Connecting</button>
            </Show>
        </div>
        <Show when={controller.state() === CameraState.connected}>
            <img class={styles.camera} src={cameraAddress()} />
        </Show>
    </>
}
