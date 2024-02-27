import { Accessor, Setter, createEffect, onCleanup, onMount } from "solid-js";
import styles from './CodeEditor.module.css'

import { EditorView, basicSetup } from "codemirror"
import { keymap } from "@codemirror/view"
import { python } from "@codemirror/lang-python"
import { oneDarkTheme } from "@codemirror/theme-one-dark"
import { throttle } from "underscore"

const codeHelp = `

# Drive Forward
robot.drivetrain.set_speed(direction=Motor.DIRECTION_FWD, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)

# Drive and turn
robot.drive(direction=Motor.DIRECTION_FWD, rotation=3, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
robot.turn(direction=Motor.DIRECTION_LEFT, rotation=90, unit_rotation=Motor.UNIT_TURN_ANGLE, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)

# Configured motor movements
robot.motors["motor1"].move(direction=Motor.DIRECTION_FWD, amount=3, unit_amount=Motor.UNIT_SEC, limit=75, unit_limit=Motor.UNIT_SPEED_RPM)
robot.motors["motor1"].spin(direction=Motor.DIRECTION_FWD, rotation=75, unit_rotation=Motor.UNIT_SPEED_RPM)
robot.motors["motor1"].stop(action=Motor.ACTION_STOP_AND_HOLD)
robot.motors["motor1"].motor.stop(action=Motor.ACTION_RELEASE)

for motor in robot.motors:
  motor.stop(action=Motor.ACTION_RELEASE)

# Reading sensors:
distance = robot.sensors["distance_sensor"].read()
gyro = robot.imu.orientation["yaw"]
color = robot.read_color(1) # 1-4
button = robot.sensors["button"].read()

# LEDs
robot.led.set(leds=[1,2,3], color=(robot.read_color(1)))
robot.led.start_animation(RingLed.Siren)`


function CodeEditor({ value, setValue }: { value: Accessor<string>, setValue: Setter<string> }) {

  let editorRef: HTMLDivElement;
  let editor: EditorView;

  const initVal = value()

  const saveNow = () => {
    const newCode = editor.state.doc.toString()
    setValue(newCode)
  }
  const throttledUpdater = throttle(saveNow, 2000)

  onMount(() => {
    // Define a custom keymap for handling the Tab key
    const myKeymap = keymap.of([{
      key: "Tab",
      run: (view) => {
        // Insert 4 spaces. You can customize this action.
        view.dispatch(view.state.replaceSelection(" "));
        return true; // Indicate that the key event has been handled
      }
    }]);
    editor = new EditorView({
      extensions: [
        basicSetup,
        python(),
        myKeymap,
        oneDarkTheme,
        EditorView.updateListener.of(throttledUpdater),
        EditorView.domEventHandlers({ blur: saveNow })
      ],
      doc: value(),
      parent: editorRef

    })

  });

  onCleanup(() => {
    editor.destroy()
  })

  return <div>
    <div ref={editorRef!} class={styles.editor} />
    <pre class={styles.pre}>
      {codeHelp}

    </pre>
  </div>
}

export default CodeEditor