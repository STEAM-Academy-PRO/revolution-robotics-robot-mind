import { Show } from "solid-js";

import styles from "./Config.module.css";

import {
  MotorConfig,
  MotorType,
  SensorConfig,
  SensorType,
  motors,
  sensors,
  setMotors,
  setSensors,
} from "../utils/Config";
import { MotorCell } from "./utils/Motor";
import { SensorCell } from "./utils/Sensor";
import SettingsView from "./SettingsView";
import { setEndpoint } from "../settings";
import { connectToRobot } from "../utils/Communicator";
import logoSide from "../assets/rr-logo-white-left.svg";

function ConfigView() {
  const addMotor = (index: number) => {
    const newMotor: MotorConfig = {
      reversed: 0,
      name: `motor${index + 1}`,
      type: MotorType.DRIVE,
      side: 0,
    };
    const newMotorArray = motors().slice();
    newMotorArray.splice(index, 1, newMotor);
    setMotors(newMotorArray);
  };
  const updateMotor = (index: number, motor: MotorConfig) => {
    const newMotorArray = motors().slice();
    newMotorArray.splice(index, 1, Object.assign({}, motor));
    setMotors(newMotorArray);
  };
  const removeMotor = (index: number) => {
    const newMotorArray = motors().slice();
    newMotorArray.splice(index, 1, null);
    setMotors(newMotorArray);
  };

  const addSensor = (index: number) => {
    const newSensor: SensorConfig = {
      name: `sensor${index + 1}`,
      type: SensorType.BUTTON,
    };
    const newSensorArray = sensors().slice();
    newSensorArray.splice(index, 1, newSensor);
    setSensors(newSensorArray);
  };
  const updateSensor = (index: number, sensor: SensorConfig) => {
    const newSensorArray = sensors().slice();
    newSensorArray.splice(index, 1, Object.assign({}, sensor));
    setSensors(newSensorArray);
  };

  const removeSensor = (index: number) => {
    const newSensorArray = sensors().slice();
    newSensorArray.splice(index, 1, null);
    setSensors(newSensorArray);
  };

  return (
    <div>
      <div class={styles.controller}>
        <div class={styles.configWrapper}>
          <div class={styles.config}>
            <div class={styles.motorRows}>
              <div class={styles.motorRow}>
                {[0, 1, 2].map((i) => (
                  <MotorCell
                    index={i}
                    motors={motors()}
                    addMotor={addMotor}
                    updateMotor={updateMotor}
                    removeMotor={removeMotor}
                  ></MotorCell>
                ))}
              </div>
              <div class={styles.motorPad}>
                <img src={logoSide} alt="Logo" class={styles.logo} />
              </div>
              <div class={styles.motorRow}>
                {[3, 4, 5].map((i) => (
                  <MotorCell
                    index={i}
                    motors={motors()}
                    addMotor={addMotor}
                    updateMotor={updateMotor}
                    removeMotor={removeMotor}
                  ></MotorCell>
                ))}
              </div>
            </div>
          </div>
          <div class={styles.config}>
            <div class={styles.sensorList}>
              {[0, 1, 2, 3].map((i) => (
                  <SensorCell
                    index={i}
                    sensors={sensors()}
                    addSensor={addSensor}
                    updateSensor={updateSensor}
                    removeSensor={removeSensor}
                  />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ConfigView;
