import {
  createSignal,
  createEffect,
  Accessor,
  Setter,
  Show,
  createMemo,
  onCleanup,
} from "solid-js";
import { RobotMessage, WSEventResult, WSEventType } from "../utils/Communicator";
import { Position } from "../utils/Position";
import { mapAnalogNormal, toByte } from "../utils/mapping";
import { Joystick } from "../components/Joystick";
import { CameraView } from "./CameraView";
import { Log, log } from "../utils/log";
import { SensorType, SensorTypeResolve, currentConfig } from "../utils/Config";
import { uploadConfig } from "../utils/commands";
import { ColorSensor, ColorSensorReading } from "../utils/ColorSensor";
import { conn } from "../settings";

import styles from "./Play.module.css";
import {
  processVoiceCommandTranscript,
  SpeechRecognition,
} from "../utils/voice-command";
import { Toast } from "./utils/Toast";

const BUTTON_MAP_XBOX: { [id: number]: number } = {
  2: 0,
  3: 2,
  0: 3,
  1: 1,
};

export default function PlayView({
  isActive,
}: {
  isActive: Accessor<boolean>;
}) {
  const [orientation, setOrientation] = createSignal<string>();
  const [battery, setBattery] = createSignal<Array<number>>();
  const [version, setVersion] = createSignal<string>();
  const [hasGamepad, setHasGamepad] = createSignal<boolean>(false);
  const [isConnected, setIsConnected] = createSignal<boolean>(true);
  const [controlSignal, setControlSignal] = createSignal<string>("");
  const [turnaround, setTurnaround] = createSignal<number>(0);
  const [orderError, setOrderError] = createSignal<number>(0);
  const [isListening, setIsListening] = createSignal<boolean>(false);
  const [toast, setToast] = createSignal<string>("");
  // True if a control message was sent within the last second
  const [hadRecentControl, setHadRecentControl] = createSignal<boolean>(false);

  let lastTimeControlMessageSent: number = new Date().getTime();
  let lastControlMessageId: number = 0;
  let lastTimeControlConfirmReceived: number = new Date().getTime();

  interface SensorView {
    value: Accessor<any>;
    setValue: Accessor<any>;
    type: SensorType;
  }

  // Render sensors based on the config!
  const sensors: Accessor<{ [id: number]: SensorView }> = createMemo(() => {
    const sensors: { [id: number]: SensorView } = {};
    currentConfig().robotConfig.sensors.map((config, i) => {
      if (config) {
        const [value, setValue] = createSignal();
        sensors[i + 1] = { value, setValue, type: config.type };
      }
    });
    return sensors;
  });

  const reUploadConfig = () => {
    console.log('reUploadConfig', currentConfig());
    uploadConfig(conn(), currentConfig());
    // setIsConnected(true);
    sendControlMessage();
  };

  window.addEventListener("gamepadconnected", (event) => {
    log("✅ 🎮 A gamepad was connected");
    setHasGamepad(true);
  });
  window.addEventListener("gamepaddisconnected", (event) => {
    log("❌ 🎮 A gamepad was disconnected:");
    setHasGamepad(false);
  });

  const buttons = [0, 1, 2, 3].map((i) => {
    let [get, set] = createSignal<boolean>(false);
    let [status, setStatus] = createSignal<number>(0);
    return { get, set, status, setStatus };
  });

  const sendCommand = (command: string) => {
    if (!isActive() || !isConnected()) {
      return;
    }
    // log(`Sending command: ${command}`);
    conn()?.send(RobotMessage.run, command);
  };

  if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = true; // or true for continuous listening

    createEffect(async () => {
      if (isListening()) {
        recognition.start();
      } else {
        recognition.stop();
      }
    }, [isListening]);

    recognition.onresult = (event: any) => {
      // console.log("AI RC recognition result:", event);
      let fullTranscript = "";
      for (let i = 0; i < event.results.length; i++) {
        fullTranscript += event.results[i][0].transcript + "\n";
      }
      const lastCommand = event.results[event.results.length - 1][0].transcript;

      // Find last command:
      setToast("🎤 " + lastCommand);
      log("🎤 " + lastCommand);
      // console.log("Last command:", lastCommand);
      const pythonCode = processVoiceCommandTranscript(lastCommand);
      if (pythonCode) {
        // console.log('Sending command from voice:', pythonCode);
        sendCommand(pythonCode);
      }
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event);
      if (event.error === "audio-capture") {
        setToast(
          "Error: No microphone found. Try setting it under chrome://settings/content/microphone"
        );
        log(
          "Error: No microphone found. Try setting it under chrome://settings/content/microphone"
        );
      }
      setToast(`Error: ${event.error}`);
      log(`Error: ${event.error}`);
      setIsListening(false);
    };

    recognition.onend = () => {
      console.log("Speech recognition ended");
      if (isListening()) {
        setTimeout(() => {
          if (isListening()) {
            recognition.start();
          }
        }, 100);
      }
    };
  }

  const BUFFER = 256;
  const turnaroundArray = new Array(BUFFER).fill(0);

  // Process incoming messages.
  createEffect(() => {
    conn()?.on(WSEventType.onMessage, (data: WSEventResult) => {
      switch (data.event) {
        case "confirm_success":
          setTimeout(()=>sendControlMessage(), 100);
          break;
        case "control_confirm":
          // Ready for the next control message.
          const now = new Date().getTime();
          if (data.data !== lastControlMessageId) {
            // console.log("Order error", data.data, lastControlMessageId)
            setOrderError(orderError() + 1);
          }
          turnaroundArray[data.data] = now - lastTimeControlMessageSent;

          setTurnaround(
            Math.round(turnaroundArray.reduce((a, b) => a + b, 0) / BUFFER)
          );
          // Mark the time we received the last confirmation
          lastTimeControlConfirmReceived = now;
          // Small delay to have at least some ms between messages.
          setTimeout(() => sendControlMessage(), 10);
          break;
        case "orientation_change":
          setOrientation(
            `X: ${data.data.a} Y: ${data.data.c} Z: ${data.data.b}`
          );
          break;
        case "battery_change":
          setBattery(data.data);
          break;
        case "version_info":
          setVersion(
            Object.keys(data.data)
              .map((k) => `${k}: ${data.data[k]}`)
              .join(" ")
          );
          break;
        case "program_status_change":
          buttons[data.data[0]].setStatus(data.data[1]);
          break;
        case "controller_lost":
          if (isConnected()){
            reUploadConfig()
          }
          break;
        case "sensor_value_change":
          const sensorId = data.data.port_id + 1;
          const sensorValue = data.data.value;
          const sensorType = sensors()[sensorId]?.type;
          switch (sensorType) {
            case SensorType.BUTTON:
              sensors()[sensorId].setValue(sensorValue ? "1" : "0");
              break;
            case SensorType.COLOR:
              const colorReadings: ColorSensorReading = sensorValue;
              sensors()[sensorId].setValue(colorReadings);
              break;
            default:
              if (sensors()[sensorId]) {
                sensors()[sensorId].setValue(sensorValue);
              }
          }
          break;
        case "error":
          break;
        case "run_confirm":
          break;
        default:
          console.log(`[message] Data received from server: ${data.event}`);
      }
    });
    setIsConnected(Boolean(conn()));
    // if (conn()){
    //   sendControlMessage()
    // }
  });

  // Maintain hadRecentControl() based on lastTimeControlMessageSent
  createEffect(() => {
    const id = setInterval(() => {
      const now = new Date().getTime();
      setHadRecentControl(now - lastTimeControlMessageSent <= 1000);
    }, 200);
    onCleanup(() => clearInterval(id));
  });

  // Watchdog: if no control confirmation received in 100ms, send a new control message
  createEffect(() => {
    const id = setInterval(() => {
      if (!isActive() || !isConnected()) return;
      const now = new Date().getTime();
      if (now - lastTimeControlConfirmReceived > 100) {
        setOrderError(orderError() + 10);
        console.warn('Control Message Error')
        // sendControlMessage();
      }
    }, 100);
    onCleanup(() => clearInterval(id));
  });

  const position = new Position();
  const position2 = new Position();

  let i = 0;

  let last = { x: 0, y: 0 };
  let last2 = { x: 0, y: 0 };

  // We have to send the control messages whenever we uploaded it, or else it resets configuration state.
  // Try uncommenting the lines with doSendMove in them. The first time it stops receiving the messages
  // on the robot the state resets to not configured.

  const updatePositionsFromGamepad = () => {
    const gamepads = navigator.getGamepads();
    for (const gamepad of gamepads) {
      // Disregard empty slots.
      if (!gamepad) {
        continue;
      }
      // Analog controls for drive.
      position.setX(gamepad.axes[0] * 0.8);
      position.setY(-gamepad.axes[1] * 0.8);

      // 2nd joystick
      position2.setX(gamepad.axes[2] * 0.8);
      position2.setY(-gamepad.axes[3] * 0.8);

      // Process the gamepad buttons, map them to the controller. See map up there.
      Object.keys(BUTTON_MAP_XBOX).map((keySrt) => {
        const key = parseInt(keySrt);
        const value = gamepad.buttons[BUTTON_MAP_XBOX[key]].pressed;
        buttons[key].set(value);
      });
    }
  }

  // Timer loop: keep polling controller to update positions/buttons even if no messages are sent
  createEffect(() => {
    let rafId = 0;
    const loop = () => {
      // Update local positions/buttons from controller regardless of messaging cadence
      if (hasGamepad() && isActive()) {
        updatePositionsFromGamepad();
      }
      rafId = requestAnimationFrame(loop);
    };
    rafId = requestAnimationFrame(loop);
    onCleanup(() => cancelAnimationFrame(rafId));
  });


  const sendControlMessage = () => {
    if (!isActive() || !isConnected()) {
      return;
    }

    last.x = position.x();
    last.y = position.y();

    last2.x = position2.x();
    last2.y = position2.y();

    // Only allow gamepad, if we are not having the joystick on the screen
    // set to a value to avoid flickering.
    // const isScreenControllerIsAtCenter = (!position.x() && !position.y())

    const twoOtherAnalogs = { x: 0, y: 0 };

    // Gamepad support!
    if (hasGamepad()) {
      updatePositionsFromGamepad()
    }

    const buttonByte = toByte(buttons.map((b) => b.get()));

    const controlMessageId = i++ % 127; // keepalive - no need to change this as it's bluetooth specific

    const ctrlArray = new Uint8Array([
      controlMessageId,
      mapAnalogNormal(position.x()), // UInt8, left-right analog, value range: 0-255
      mapAnalogNormal(position.y()), // UInt8, bottom-top analog, value range: 0-255

      mapAnalogNormal(position2.x()), // UInt8, left-right analog, value range: 0-255
      mapAnalogNormal(position2.y()), // UInt8, bottom-top analog, value range: 0-255
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
    ]);

    isActive() && conn()?.send(RobotMessage.control, ctrlArray);
    const now = new Date().getTime();
    setControlSignal(
      ctrlArray.join("") + " " + (now - lastTimeControlMessageSent) + "ms"
    );
    lastTimeControlMessageSent = now;
    lastControlMessageId = controlMessageId;
    setHadRecentControl(true);
  };

  // onCleanup(() => {
  //   clearInterval(interval)
  // })

  return (
    <div>
      <CameraView>
        <Toast message={toast}></Toast>
        <div class={styles.playView}>
          <div class={styles.statuses}>
            <span class={styles.status}>version: {version()}</span>
            <span class={styles.status}>
              orientation:{" "}
              <pre style={{ margin: 0 }} innerHTML={orientation()}></pre>
            </span>
            <span class={styles.status}>battery: {battery()?.join(" ")}</span>
            {Object.keys(sensors()).map((sensorKey) => (
              <span class={styles.status}>
                <SensorView
                  type={SensorTypeResolve[sensors()[sensorKey].type]}
                  value={sensors()[sensorKey].value}
                ></SensorView>
              </span>
            ))}

            <span class={styles.status}>
              <span> Turnaround: {turnaround()}ms </span>
              <div
                class={styles.error}
                title="... meaning the message confirmations come back in the wrong order."
              >
                M. Order Error: <div>{orderError()}</div>
              </div>
            </span>

            <span class={styles.status}>
              <button
                class={styles.listenButton}
                classList={{ [styles.listening]: isListening() }}
                onClick={() => {
                  setIsListening(!isListening());
                }}
              >
                <Show when={isListening()}>Stop Listening</Show>
                <Show when={!isListening()}>Start Listening</Show>
              </button>
            </span>

            <span class={styles.status}>
              <Show when={isConnected()}>
                Connected 🔌 <br />
                {/* <div>ctrl: {controlSignal()}</div> */}
              </Show>
              <Show when={hadRecentControl()}>🟢</Show>
              <Show when={!hadRecentControl()}>🔴</Show>
              <Show when={!isConnected()}>Disconnected 🚫</Show>

              <Show when={conn()}>
                <div>
                  <button onClick={()=>reUploadConfig()}>RESTART</button>
                </div>
              </Show>
            </span>
          </div>
          <div class={styles.controller}>
            <div class={styles.joystick}>
              <Joystick enabled={isConnected} position={position}></Joystick>
              <Joystick enabled={isConnected} position={position2}></Joystick>
            </div>
            <div class={styles.placeholder}></div>
            <div class={styles.controllerButtons}>
              <Buttons list={buttons} />
            </div>
          </div>
          {/* <div>
            <Log />
          </div> */}
        </div>
      </CameraView>
    </div>
  );
}

function SensorView({ type, value }: { value: Accessor<any>; type: string }) {
  return (
    <div>
      {type} <br />
      <Show when={type === "button"}>{value()}</Show>
      <Show when={type === "distance_sensor"}>{value()}</Show>
      <Show when={type === "color_sensor"}>
        <ColorSensor value={value}></ColorSensor>
      </Show>
    </div>
  );
}

function Button({
  label,
  setter,
  getter,
  status,
}: {
  label: string;
  setter: Setter<boolean>;
  getter: Accessor<boolean>;
  status: Accessor<number>;
}) {
  return (
    <button
      class={styles.button}
      classList={{
        [styles.buttonPressed]: getter(),
        [styles.buttonError]: status() === 2,
        [styles.buttonRunning]: status() === 1,
      }}
      onTouchStart={() => setter(true)}
      onTouchEnd={() => setter(false)}
      onMouseDown={() => setter(true)}
      onMouseUp={() => setter(false)}
    >
      {label}
    </button>
  );
}

function Buttons({
  list,
}: {
  list: Array<{
    set: Setter<boolean>;
    get: Accessor<boolean>;
    status: Accessor<number>;
  }>;
}) {
  const rows = [0, 1, 2];
  const cols = [0, 1, 2];

  const matrix = [
    [5, 0, 6],
    [3, 4, 1],
    [8, 2, 7],
  ];

  function getButtonForIndex(i: number) {
    if (i < list.length) {
      return (
        <Button
          label={String(i)}
          setter={list[i].set}
          status={list[i].status}
          getter={list[i].get}
        />
      );
    }
  }

  return (
    <div class={styles.matrix}>
      {rows.map((row) => (
        <div key={row} class={styles.matrixRow}>
          {cols.map((col) => (
            <div key={col} class={styles.matrixCell}>
              {getButtonForIndex(matrix[row][col])}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
