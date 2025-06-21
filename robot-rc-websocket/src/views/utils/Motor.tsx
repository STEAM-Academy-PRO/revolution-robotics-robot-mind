import { Show, createEffect, createSignal } from "solid-js";
import { MotorConfig, MotorReversed, MotorSide, MotorType, SensorConfig } from "../../utils/Config";

import styles from "../Config.module.css";

export function MotorCell(props: {
  index: number;
  motors: (MotorConfig | null)[];
  addMotor: (index: number) => void;
  updateMotor: (index: number, motor: MotorConfig) => void;
  removeMotor: (index: number) => void;
}) {
  const [motor, setMotor] = createSignal<MotorConfig | null>(
    props.motors[props.index]
  );
  createEffect(() => {
    setMotor(props.motors[props.index]);
  });

  const toggleMotor = () => {
    if (motor()) {
      props.removeMotor(props.index);
    } else {
      props.addMotor(props.index);
    }
  };

  return (
    <div class={styles.portCell}>
      <button
        class={styles.portButton}
        classList={{ [styles.activeButton]: !!motor() }}
        onClick={toggleMotor}
      >
        Motor {props.index + 1}
      </button>
      <Show when={motor()}>
        <MotorView
          motor={motor()!}
          update={(m) => props.updateMotor(props.index, m)}
        />
      </Show>
    </div>
  );
}

export function MotorView({
  motor,
  update,
}: {
  motor: MotorConfig;
  update: (motor: MotorConfig) => void;
}) {
  const [reversed, setReversed] = createSignal<number>(motor.reversed);
  const [type, setType] = createSignal<number>(motor.type);
  const [side, setSide] = createSignal<number>(motor.side);

  const updateMotor = () => {
    motor.reversed = reversed();
    motor.type = type();
    motor.side = side();
      update(motor);
  }

  const updateType = (newType: MotorType) => {
    setType(newType);
    updateMotor();
  }

  const updateSide = (newSide: MotorSide) => {
    setSide(newSide);
    updateMotor();
  }
  const updateReversed = (newReversed: MotorReversed) => {
    setReversed(newReversed);
    updateMotor();
  }




  return (
    <div>
      <div>
        <a
          class={styles.clickable}
          classList={{ [styles.bold]: type() === MotorType.MOTOR }}
          onClick={() => updateType(MotorType.MOTOR)}
        >
          MOTOR
        </a>
        /
        <a
          class={styles.clickable}
          classList={{ [styles.bold]: type() === MotorType.DRIVE }}
          onClick={() => updateType(MotorType.DRIVE)}
        >
          DRIVE
        </a>
      </div>
      <Show when={type() === MotorType.DRIVE}>
        <div>
          <a
            class={styles.clickable}
            classList={{ [styles.bold]: side() === MotorSide.LEFT }}
            onClick={() => updateSide(MotorSide.LEFT)}
          >
            left{" "}
          </a>
          <a
            class={styles.clickable}
            classList={{ [styles.bold]: side() === MotorSide.RIGHT }}
            onClick={() => updateSide(MotorSide.RIGHT)}
          >
            right
          </a>
        </div>
        <div>
          <a
            class={styles.clickable}
            classList={{ [styles.bold]: reversed() === MotorReversed.TRUE }}
            onClick={() => updateReversed(MotorReversed.TRUE)}
          >
            yes{" "}
          </a>
          <a
            class={styles.clickable}
            classList={{ [styles.bold]: reversed() === MotorReversed.FALSE }}
            onClick={() => updateReversed(MotorReversed.FALSE)}
          >
            no
          </a>
        </div>
      </Show>
    </div>
  );
}
