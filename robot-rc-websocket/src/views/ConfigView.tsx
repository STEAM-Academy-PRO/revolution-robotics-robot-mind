import { Show } from 'solid-js'

import styles from './Config.module.css'

import { MotorConfig, MotorType, SensorConfig, SensorType, motors, sensors, setMotors, setSensors } from '../utils/Config';
import { MotorView } from '../utils/Motor';
import { SensorView } from '../utils/Sensor';
import SettingsView from './SettingsView';

function ConfigView() {

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
  const updateSensor = (index: number, sensor: SensorConfig) => {
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
            <SettingsView />
          </div>

        </div>
        <div class={styles.config}>
          <h3>Sensors</h3>
          <table class={styles.configurationTable}>
            <thead>
              <tr>
                <td>Index</td>
                <td>Type</td>
              </tr>
            </thead>
            <tbody>
              {sensors().map((s, i) => (<tr>
                <td>{i + 1}</td>
                <td>{!s ? (
                  <><button onClick={() => addSensor(i)}>➕</button></>) :
                  <button onClick={() => removeSensor(i)}>🗑</button>
                }</td>
                <td><Show when={s}>
                  <SensorView sensor={s} update={(sensor) => updateSensor(i, sensor)} />
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
                    <><button onClick={() => addMotor(i)}>➕</button></>) :
                    <button onClick={() => removeMotor(i)}>🗑</button>
                  }</td>
                  <td><Show when={s}>
                    <MotorView motor={s} update={(motor) => updateMotor(i, motor)}></MotorView>
                  </Show>
                  </td>
                </tr>)
              )}
            </tbody>
          </table>
        </div>

      </div>
    </div>
  );
}

export default ConfigView;
