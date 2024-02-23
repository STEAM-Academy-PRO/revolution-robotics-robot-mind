import { createSignal, createEffect, onCleanup, Accessor, Setter, Show } from 'solid-js'
import { RobotMessage, SocketWrapper, WSEventType } from '../utils/Communicator';
import { Position } from '../utils/Position';
import { mapAnalogNormal, toByte } from '../utils/mapping';
import { Joystick } from '../components/Joystick';
import styles from './Controller.module.css'
import { CameraView } from './CameraView';
import { clearLog, getLog, log } from '../utils/log';
import { RobotConfig, SensorType, SensorTypeResolve } from '../utils/Config';
import { uploadConfig } from '../utils/commands';
import { ColorSensor, ColorSensorReading } from '../utils/ColorSensor';

const BUTTON_MAP_XBOX: { [id: number]: number } = {
  2: 0,
  3: 2,
  0: 3,
  1: 1
}

export default function ControllerView({
  conn, isActive,
  endpoint,
  config,
}: {
  conn: Accessor<SocketWrapper | null>, isActive: Accessor<boolean>,
  endpoint: Accessor<string>,
  config: Accessor<RobotConfig>
}) {

  const [orientation, setOrientation] = createSignal<Array<number>>()
  const [battery, setBattery] = createSignal<Array<number>>()
  const [version, setVersion] = createSignal<string>()
  const [hasGamepad, setHasGamepad] = createSignal<boolean>(false)
  const [isConnected, setIsConnected] = createSignal<boolean>(true)

  // Extend the values!
  const sensors: { [id: number]: { value: Accessor<any>, setValue: Accessor<any>, type: SensorType } } = {}
  config().robotConfig.sensors.map(
    (config, i) => {
      if (config) {
        const [value, setValue] = createSignal()
        sensors[i + 1] = { value, setValue, type: config.type }
      }
    })

  const reUploadConfig = () => {
    uploadConfig(conn(), config())
    setIsConnected(true)
  }

  let logElement: HTMLPreElement;

  createEffect(() => {
    getLog()
    if (logElement) {
      logElement.scrollTop = logElement.scrollHeight
    }
  })

  window.addEventListener('gamepadconnected', (event) => {
    log('✅ 🎮 A gamepad was connected');
    setHasGamepad(true)
  });
  window.addEventListener('gamepaddisconnected', (event) => {
    log('❌ 🎮 A gamepad was disconnected:');
    setHasGamepad(false)
  });

  const buttons = [0, 1, 2, 3].map((i) => {
    let [get, set] = createSignal<boolean>(false)
    let [status, setStatus] = createSignal<number>(0)
    return { get, set, status, setStatus }
  })

  const [motorAngles, setMotorAngles] = createSignal<Array<number>>([0, 0, 0, 0, 0, 0])

  // Process incoming messages.
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
          setVersion(Object.keys(data.data).map((k) => `${k}: ${data.data[k]}`).join(' '))
          break
        case 'program_status_change':
          buttons[data.data[0]].setStatus(data.data[1])
          break
        case 'controller_lost':
          setIsConnected(false)
          break
        case 'sensor_value_change':
          const sensorId = data.data.port_id
          const sensorValue = data.data.value
          switch (sensors[sensorId].type) {
            case SensorType.BUTTON:
              sensors[sensorId].setValue(sensorValue ? '1' : '0')
              break
            case SensorType.COLOR:
              console.log('color sensor', sensorValue)
              const colorReadings: ColorSensorReading = sensorValue
              sensors[sensorId].setValue(colorReadings)
              break
            default:
              sensors[sensorId].setValue(sensorValue)

          }
          break
        default:
          console.log(`[message] Data received from server: ${data.event}`);
      }
    })
    setIsConnected(Boolean(conn()))
  })

  const position = new Position()

  let i = 0

  let last = { x: 0, y: 0 }

  // We have to send the control messages whenever we uploaded it, or else it resets configuration state.
  // Try uncommenting the lines with doSendMove in them. The first time it stops receiving the messages
  // on the robot the state resets to not configured.

  const interval = setInterval(() => {
    if (!isActive() || !isConnected()) { return }

    last.x = position.x()
    last.y = position.y()

    // Only allow gamepad, if we are not having the joystick on the screen
    // set to a value to avoid flickering.
    // const isScreenControllerIsAtCenter = (!position.x() && !position.y())

    const twoOtherAnalogs = { x: 0, y: 0 }

    // Gamepad support!
    if (hasGamepad()) {
      const gamepads = navigator.getGamepads();
      for (const gamepad of gamepads) {
        // Disregard empty slots.
        if (!gamepad) { continue; }
        // Analog controls for drive.
        position.setX(gamepad.axes[0] * 0.8)
        position.setY((-gamepad.axes[1]) * 0.8)
        twoOtherAnalogs.x = gamepad.axes[2]
        twoOtherAnalogs.y = gamepad.axes[3]

        // Process the gamepad buttons, map them to the controller. See map up there.
        Object.keys(BUTTON_MAP_XBOX).map((keySrt) => {
          const key = parseInt(keySrt)
          const value = gamepad.buttons[BUTTON_MAP_XBOX[key]].pressed
          buttons[key].set(value)
        })
      }
    }

    const buttonByte = toByte(buttons.map((b) => b.get()))

    const ctrlArray = new Uint8Array([
      i++ % 127, // keepalive - no need to change this as it's bluetooth specific
      mapAnalogNormal(position.x()), // UInt8, left-right analog, value range: 0-255
      mapAnalogNormal(position.y()), // UInt8, bottom-top analog, value range: 0-255

      twoOtherAnalogs.x, // Gamepad 2 analog
      twoOtherAnalogs.y, // Gamepad 3 analog
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
  }, 25)

  onCleanup(() => {
    clearInterval(interval)
  })


  return (
    <div>
      <h1>
        Controller
      </h1>
      <span class={styles.controllerConnection}>
        <Show when={isConnected()}>Connected 🔌</Show>
        <Show when={!isConnected()}>
          Disconnected 🚫
          <Show when={conn()}>
            <button onClick={reUploadConfig}>RESTART</button>
          </Show>
        </Show>
      </span>
      <div class={styles.statuses}>
        <span class={styles.status}>version: {version()}</span>
        <span class={styles.status}>orientation: {JSON.stringify(orientation())}</span>
        <span class={styles.status}>battery: {battery()?.join(' ')}</span>
        <span class={styles.status}>motor angles: {motorAngles()?.join(' ')}</span>
        {Object.keys(sensors).map((sensorKey) => (
          <span class={styles.status}>
            <SensorView type={SensorTypeResolve[sensors[sensorKey].type]}
              value={sensors[sensorKey].value}
            ></SensorView>
          </span>
        ))}
      </div>
      <div class={styles.controller}>
        <div class={styles.joystick}>
          <Joystick enabled={isConnected} position={position}></Joystick>
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
        <Show when={getLog()}>
          <button onClick={() => clearLog()}>clear</button>
        </Show>
        <pre ref={logElement} class={styles.log}>
          {getLog()}
        </pre>
      </div>
    </div>
  );
}

function SensorView({ type, value }: { value: Accessor<any>, type: string }) {
  return <div>
    {type}
    <Show when={type === 'button'}>
      {value()}
    </Show>
    <Show when={type === 'distance_sensor'}>
      {value()}
    </Show>
    <Show when={type === 'color_sensor'}>
      <ColorSensor value={value}></ColorSensor>
    </Show>
  </div>
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