import { createEffect, createSignal, onCleanup, onMount } from "solid-js";
import styles from "./AiRcView.module.css";
import { BlocklyView } from "./BlocklyView";
import aiBlocklyPrompt from "./utils/ai-blockly-prompt";
import { fetchAiResponse } from "../utils/ai";

const codeHelp = `

# Drive Forward
robot.drivetrain.set_speed(direction=Motor.DIRECTION_FWD, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)

# Drive and turn
robot.drive(direction=Motor.DIRECTION_BACK, rotation=3, unit_rotation=Motor.UNIT_SEC, speed=75, unit_speed=Motor.UNIT_SPEED_RPM)
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
robot.led.start_animation(RingLed.Siren)`;

function AiRcView() {
  const SpeechRecognition = window.webkitSpeechRecognition;
  // if (typeof window['SpeechRecognition'] === 'undefined') {
  //   console.error('SpeechRecognition is not supported in this browser.');
  //   return <div>Speech Recognition is not supported in this browser.</div>;
  // }
  const recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.continuous = true; // or true for continuous listening
  recognition.interimResults = true;

  let promptEditorRef!: HTMLTextAreaElement;

  let lastXml = localStorage.getItem("ai-rc-code") || "";

  const [isListening, setIsListening] = createSignal(false);
  const [text, setText] = createSignal<string>(
    "go forward 30cm then turn right and repeat this 4 times"
  );
  const [isPromptEditorOpen, setIsPromptEditorOpen] =
    createSignal<boolean>(false);
  const [isLoadingPrompt, setIsLoadingPrompt] = createSignal<boolean>(false);

  onMount(() => {
    // console.log('ai stub')
  });

  onCleanup(() => {
    // console.log('ai stub exit')
  });

  const onSave = (code: string) => {
    // console.log('AI RC code saved:', code, arguments);
    localStorage.setItem("ai-rc-code", code);
    // setXml(code);
  };

  recognition.onresult = (event: any) => {
    let fullTranscript = "";
    for (let i = 0; i < event.results.length; i++) {
      fullTranscript += event.results[i][0].transcript + "n";
    }
    console.log("Recognized:", fullTranscript);
    setText(fullTranscript);
    // setText(transcript);
  };

  createEffect(async () => {
    if (isListening()) {
      console.log("AI RC listening started");
      recognition.start();
    } else {
      // console.log('AI RC listening stopped');
      recognition.stop();
      // TODO: send it up to the GPT endpoint
      const code = text();

      console.log(import.meta.env.VITE_OPENAI_API_KEY, " - ", code);
    }
  }, [isListening]);

  const sendQuery = async () => {
    if (isLoadingPrompt()) {
      return;
    }
    setIsLoadingPrompt(true);
    setXml("");
    const responseJson = await fetchAiResponse(text());

    console.log("AI RC response:", responseJson);
    setXml(responseJson.xml);
    setIsLoadingPrompt(false);
    // TODO: send the code to the robot and run it!
  };

  const reloadCode = (code: string) => {
    // TODO: upload config and run python!
    console.log("Should send robot this code and run:", code);
  };

  const [xml, setXml] = createSignal<string>(lastXml);

  return (
    <div>
      <button
        class={styles.ai}
        classList={{ [styles.listening]: isListening() }}
        disabled={isLoadingPrompt()}
        onClick={() => {
          setIsListening(!isListening());
          setIsPromptEditorOpen(false);
          if (!isListening()) {
            sendQuery();
          }
        }}
      >
        Robot Friend
      </button>

      <button
        class={styles.textButton}
        onClick={() => {
          setIsPromptEditorOpen(!isPromptEditorOpen());
          if (!isPromptEditorOpen()) {
            sendQuery();
          }
        }}
      >
        <span class={styles.icon} role="img" aria-label="keyboard">
          ⌨️
        </span>
      </button>

      <div></div>
      {text() && (
        <div
          class={styles.prompt}
          innerHTML={text().replace(/n/g, "<br />")}
        ></div>
      )}
      {isPromptEditorOpen() && (
        <div class={styles.promptEditor}>
          <textarea
            ref={promptEditorRef}
            value={text()}
            onInput={(e) => {
              setText(e.currentTarget.value);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                setIsPromptEditorOpen(false);
                sendQuery();
              }
            }}
          ></textarea>
        </div>
      )}

      <BlocklyView
        onSave={onSave}
        xml={xml}
        reloadCode={reloadCode}
      ></BlocklyView>
    </div>
  );
}

export default AiRcView;
