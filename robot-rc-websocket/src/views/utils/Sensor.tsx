import { createEffect, createSignal, Show } from "solid-js";
import { SensorConfig, SensorType, SensorTypeResolve } from "../../utils/Config";

import styles from '../Config.module.css'


export function SensorCell(props: {
  index: number;
  sensors: (SensorConfig | null)[];
  addSensor: (index: number) => void;
  updateSensor: (index: number, sensor: SensorConfig) => void;
  removeSensor: (index: number) => void;
}) {
  const [sensor, setSensor] = createSignal<SensorConfig | null>(
    props.sensors[props.index]
  );
  createEffect(() => {
    setSensor(props.sensors[props.index]);
  });

  const toggleSensor = () => {
    if (sensor()) {
      props.removeSensor(props.index);
    } else {
      props.addSensor(props.index);
    }
  };

  return (
    <div class={styles.portCell}>
      <button
        class={styles.portButton}
        classList={{ [styles.activeButton]: !!sensor() }}
        onClick={toggleSensor}
      >
        Sensor {props.index + 1}
      </button>
      <Show when={sensor()}>
        <Show when={sensor()}>
            <SensorView
              sensor={sensor()!}
              update={(sensor) => props.updateSensor(props.index, sensor)}
            />
          </Show>
      </Show>
    </div>
  );
}

export function SensorView({ sensor, update }: { sensor: SensorConfig, update: (sensor: SensorConfig) => void }) {

    const [type, setType] = createSignal<number>(sensor.type)

    const updateType = (newType: SensorType) => {
        setType(newType)
        sensor.type = newType
        sensor.name = SensorTypeResolve[newType as keyof typeof SensorTypeResolve]
        update(sensor)
    }

    return (
        <div>
            <a class={styles.clickable}
                classList={{ [styles.bold]: type() === SensorType.BUTTON }}
                onClick={() =>updateType (SensorType.BUTTON)
                  }>
                BUTTON </a>
            <a class={styles.clickable}
                classList={{ [styles.bold]: type() === SensorType.DISTANCE }}
                onClick={() =>
                    updateType(SensorType.DISTANCE)
                }>DISTANCE </a>
            <a class={styles.clickable}
                classList={{ [styles.bold]: type() === SensorType.COLOR }}
                onClick={() =>
                    updateType(SensorType.COLOR)
                }>COLOR</a>
        </div>)
}

