import { createSignal, createEffect, createMemo, onCleanup, Accessor, Setter, Show } from 'solid-js'
import { RobotMessage, SocketWrapper, WSEventType } from '../utils/Communicator';
import { Position } from '../utils/Position';
import { mapAnalogNormal, toByte } from '../utils/mapping';
import { Joystick } from '../components/Joystick';
import styles from './Controller.module.css'
import { CameraView } from './CameraView';

export default function ControllerView({
  conn, isActive,
  log, setLog,
  endpoint
}: {
  conn: Accessor<SocketWrapper | null>, isActive: Accessor<boolean>,
  log: Accessor<string>, setLog: Setter<string>, endpoint: Accessor<string>
}) {

  const [orientation, setOrientation] = createSignal<Array<number>>()
  const [battery, setBattery] = createSignal<Array<number>>()
  const [version, setVersion] = createSignal<string>()

  const buttons = [0, 1, 2, 3].map((i) => {
    let [get, set] = createSignal<boolean>(false)
    let [status, setStatus] = createSignal<number>(0)
    return { get, set, status, setStatus }
  })

  const [motorAngles, setMotorAngles] = createSignal<Array<number>>([0, 0, 0, 0, 0, 0])


  createEffect(() => {
    conn()?.on(WSEventType.onMessage, (data) => {
      switch (data.event) {
        case 'orientation_change':
          setOrientation(data.data)
          break
        case 'battery_change':
          setBattery(data.data)
          break
        case 'motor_change':
          setMotorAngles(data.data)
          break
        case 'version_info':
          setVersion(Object.keys(data.data).map((k)=>`${k}: ${data.data[k]}`).join(' '))
          break
        case 'program_status_change':
          buttons[data.data[0]].setStatus(data.data[1])
          break
        case 'program_status_change':
          buttons[data.data[0]].setStatus(data.data[1])
          break
        default:
          console.warn(`[message] Data received from server: ${data.event}`);
      }
    })
  })



  const position = new Position()

  let i = 0


  let last = { x: 0, y: 0 }


  // let doSendMove = false
  // We have to send the control messages whenever we uploaded it, or else it resets configuration state.
  // Try uncommenting the lines with doSendMove in them. The first time it stops receiving the messages
  // on the robot the state resets to not configured.

  const interval = setInterval(() => {
    // if (!on){ return }
    // const controlMessage
    // doSendMove = Boolean(last.x || last.y || (position.x() || position.y()))

    if (!isActive()) { return }

    last.x = position.x()
    last.y = position.y()

    // if (!doSendMove) { return }

    const buttonByte = toByte(buttons.map((b) => b.get()))
    // console.warn(buttonByte)

    const ctrlArray = new Uint8Array([
      i++ % 127, // keepalive - no need to change this as it's bluetooth specific
      mapAnalogNormal(position.x()), // UInt8, left-right analog, value range: 0-255
      mapAnalogNormal(position.y()), // UInt8, bottom-top analog, value range: 0-255

      0, // unused analog
      0, // unused analog
      0, // unused analog
      0, // unused analog


      0, // Reserved
      0, // Reserved
      0, // Reserved
      0, // Reserved

      buttonByte, // UInt8, button group 1, 1 button per bit
      0, // UInt8, button group 2, 1 button per bit
      0, // UInt8, button group 3, 1 button per bit
      0, // UInt8, button group 4, 1 button per bit

    ])

    isActive() && conn()?.send(RobotMessage.control, ctrlArray)
  }, 100)

  onCleanup(() => {
    clearInterval(interval)
  })


  return (
    <div>

      <h1>Controller</h1>
      <div class={styles.statuses}>
        <span class={styles.status}>version: {version()}</span>
        <span class={styles.status}>orientation: {orientation()?.join(' ')}</span>
        <span class={styles.status}>battery: {battery()?.join(' ')}</span>
        <span class={styles.status}>motor angles: {motorAngles()?.join(' ')}</span>
      </div>
      <div class={styles.controller}>
        <div class={styles.joystick}>
          <Joystick position={position}></Joystick>
        </div>
        <div class={styles.placeholder}>
          <CameraView conn={conn} endpoint={endpoint} />
        </div>
        <div class={styles.controllerButtons}>
          <Buttons list={buttons} />
        </div>
      </div>
      {/* {buttons.map((b)=>b.get()?<>1</>:<>0</>)} */}

      <div>
        <Show when={log()}>
          <button onClick={() => setLog('')}>clear</button>
        </Show>
        <pre class={styles.log}>
          {log()}
        </pre>
      </div>
    </div>
  );
}


function Button({ label, setter, getter, status }:
  { label: string, setter: Setter<boolean>, getter: Accessor<boolean>, status: Accessor<number> }) {
  return <button class={styles.button}
    classList={{
      [styles.buttonPressed]: getter(),
      [styles.buttonError]: status() === 2,
      [styles.buttonRunning]: status() === 1
    }}
    onTouchStart={() => setter(true)} onTouchEnd={() => setter(false)}
    onMouseDown={() => setter(true)} onMouseUp={() => setter(false)}>{label}</button>
}


function Buttons({ list }: { list: Array<{ set: Setter<boolean>, get: Accessor<boolean>, status: Accessor<number> }> }) {
  const rows = [0, 1, 2]
  const cols = [0, 1, 2]

  const matrix = [
    [5, 0, 6],
    [3, 4, 1],
    [8, 2, 7]
  ]

  function getButtonForIndex(i: number) {
    if (i < list.length) {
      return <Button label={String(i)} setter={list[i].set} status={list[i].status} getter={list[i].get} />
    }
  }

  return <div class={styles.matrix}>
    {rows.map((row) => (
      <div key={row} class={styles.matrixRow}>
        {cols.map((col) => (
          <div key={col} class={styles.matrixCell}>
            {getButtonForIndex(matrix[row][col])}
          </div>
        ))}
      </div>
    ))}</div>
}