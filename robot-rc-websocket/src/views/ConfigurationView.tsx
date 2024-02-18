import { createSignal, createEffect, Accessor, Setter, For, Show } from 'solid-js'

import styles from './Config.module.css'

import { RobotMessage, SocketWrapper } from '../utils/Communicator';
import { uploadConfig } from '../utils/commands';
import { BlocklyItem, DriveMode, MotorConfig, MotorType, RobotConfig, Sensor, SensorConfig, SensorType } from '../utils/Config';
import { MotorView } from '../utils/Motor';
import { SensorView } from '../utils/Sensor';

function ConfigurationView({
  config, setConfig,
  conn
}: { config: Accessor<RobotConfig>, setConfig: Setter<RobotConfig>, conn: Accessor<SocketWrapper | null> }) {

  const [driveMode, setDriveMode] = createSignal<DriveMode>(DriveMode.drive_joystick)
  const [sensors, setSensors] = createSignal<Array<SensorConfig | null>>(config().robotConfig.sensors)
  const [motors, setMotors] = createSignal<Array<MotorConfig | null>>(config().robotConfig.motors)

  const formerConfig = config()

  createEffect(()=>{
    driveMode()
    motors()
    sensors()
    const conf = Object.assign({}, formerConfig)
    conf.robotConfig.motors = motors()
    conf.robotConfig.sensors = sensors()
    setConfig(conf)
    // console.warn(conf.robotConfig.motors)
    // console.log(conf.robotConfig.sensors)
    return conf
  })

  const handleSend = () => {
    
    uploadConfig(conn(), config())
    conn()?.send(RobotMessage.configure, JSON.stringify(config(), null, 2))
  }

  const handleDriveChange = (event: Event) => {
    const target = event.target as HTMLSelectElement;
    setDriveMode(target.value as DriveMode);
    const newConfig = Object.assign({}, config()) as RobotConfig
    const driveConfigBlocklyItem = newConfig.blocklyList.find((e) => e.builtinScriptName)
    if (!driveConfigBlocklyItem) throw Error('no drive mode in condfig!')
    driveConfigBlocklyItem.builtinScriptName = target.value as DriveMode
    setConfig(newConfig)
  }

  const addMotor = (index: number) => {
    const newMotor: MotorConfig = {
      reversed: 0,
      name: `motor${index + 1}`,
      type: MotorType.DRIVE,
      side: 0
    }
    const newMotorArray = motors().slice()
    newMotorArray.splice(index, 1, newMotor)
    setMotors(newMotorArray)
  }
  const updateMotor = (index: number, motor: MotorConfig) => {
    const newMotorArray = motors().slice()
    newMotorArray.splice(index, 1, Object.assign({}, motor))
    setMotors(newMotorArray)
  }
  const removeMotor = (index: number) => {
    const newMotorArray = motors().slice()
    newMotorArray.splice(index, 1, null)
    setMotors(newMotorArray)
  }

  const addSensor = (index: number) => {
    const newSensor: SensorConfig = {
      name: `sensor${index + 1}`,
      type: SensorType.BUTTON
    }
    const newSensorArray = sensors().slice()
    newSensorArray.splice(index, 1, newSensor)
    setSensors(newSensorArray)
  }
  const updateSensor = (index: number, sensor: SensorConfig)=>{
    const newSensorArray = sensors().slice()
    newSensorArray.splice(index, 1, Object.assign({}, sensor))
    setSensors(newSensorArray)
  }

  const removeSensor = (index: number) => {
    const newSensorArray = sensors().slice()
    newSensorArray.splice(index, 1, null)
    setSensors(newSensorArray)
    
  }

  return (
    <div >
      <div class={styles.controller}>
        <div class={styles.config}>
          <div>
            <h4>Joystick mode</h4>
            <select value={driveMode()} onChange={handleDriveChange}>
              <For each={Object.values(DriveMode)}>{(mode) =>
                <option value={mode}>{mode}</option>
              }</For>
            </select>

          </div>

        </div>
        <div class={styles.config}>
          <h3>Sensors</h3>
          <table class={styles.configurationTable}>
            <thead>
              <tr>
                <td>Index</td>
                <td>Type</td>
                {/* <td>Config</td> */}
              </tr>
            </thead>
            <tbody>
              {sensors().map((s, i) => (<tr>
                <td>{i + 1}</td>
                <td>{!s ? (
                  <><button onClick={()=>addSensor(i)}>➕</button></>) : 
                  <button onClick={()=>removeSensor(i)}>🗑</button>
                  }</td>
                <td><Show when={s}>
                    <SensorView sensor={s} update={(sensor)=>updateSensor(i, sensor)}/>
                  </Show>
                </td>
              </tr>))}
            </tbody>
          </table>
        </div>
        <div class={styles.config}>
        <h3>Motors</h3>
          <table class={styles.configurationTable}>
            <thead>
              <tr>
                <td>Index</td>
                <td>Type</td>
                <td>Config</td>
              </tr>
            </thead>
            <tbody>
              {motors().map((s, i) => (
              <tr>
                <td>{i + 1}</td>
                <td>{!s ? (
                  <><button onClick={()=>addMotor(i)}>➕</button></>) : 
                  <button onClick={()=>removeMotor(i)}>🗑</button>
                  }</td>
                <td><Show when={s}>
                    <MotorView motor={s} update={(motor)=>updateMotor(i, motor)}></MotorView>  
                  </Show>
                </td>
              </tr>)
              )}
            </tbody>
          </table>
        </div>

      </div>

      {/* <pre class={styles.pre} onClick={() => setConfigString(JSON.stringify(config() || ''))}>
        {JSON.stringify(config(), null, 2)}
      </pre> */}
      {/* {response() && (
        <div>
          <h2>Response</h2>
          <pre>{JSON.stringify(response(), null, 2)}</pre>
        </div>
      )} */}
    </div>
  );
}

export default ConfigurationView;
