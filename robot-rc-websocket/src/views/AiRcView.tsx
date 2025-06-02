import { createEffect, createSignal, onCleanup, onMount } from "solid-js";
import styles from './AiRcView.module.css'
import { BlocklyView } from "./BlocklyView";

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
robot.led.start_animation(RingLed.Siren)`


const prompt = `You are a robot programming assistant for kids.
You will generate Blockly XML code for a robot control system.

Response format:
{
  "xml": "<Generated Blockly XML code here>",
  "text": "A short description of the code"
}

Motors are configured to be either drive motors, in which case the following commands are to be used:

<block type="block_drive">
  <field name="DIRECTION_SELECTOR">Motor.DIRECTION_FWD</field>
  <field name="UNIT_ROTATION_SELECTOR">Motor.UNIT_ROT</field>
  <field name="UNIT_SPEED_SELECTOR">Motor.UNIT_SPEED_RPM</field>
  <value name="ROTATION">
    <shadow type="math_number">
      <field name="NUM">3</field>
    </shadow>
  </value>
  <value name="SPEED_SLIDER">
    <shadow type="math_number">
      <field name="NUM">75</field>
    </shadow>
  </value>
</block>

DIRECTION_SELECTOR possible values:: Motor.DIRECTION_FWD, Motor.DIRECTION_BACK
UNIT_ROTATION_SELECTOR possible values: Motor.UNIT_ROT - 1 rotation is 6 cm forward for the robot.

Turning:

<block type="block_turn">
  <field name="DIRECTION_SELECTOR">Motor.DIRECTION_LEFT</field>
  <field name="UNIT_ROTATION_SELECTOR">Motor.UNIT_TURN_ANGLE</field>
  <value name="ROTATION">
    <shadow type="math_number">
      <field name="NUM">90</field>
    </shadow>
  </value>
  <value name="SPEED_SLIDER">
    <shadow type="math_number">
      <field name="NUM">75</field>
    </shadow>
  </value>
</block>

DIRECTION_SELECTOR possible values: Motor.DIRECTION_LEFT, Motor.DIRECTION_RIGHT
UNIT_ROTATION_SELECTOR possible values: Motor.UNIT_TURN_ANGLE

Motors can be moved independently with the following commands if configured:

<block type="block_turn">
  <field name="NAME_INPUT">motor1</field>
  <field name="DIRECTION_SELECTOR">Motor.DIRECTION_LEFT</field>
  <field name="UNIT_ROTATION_SELECTOR">Motor.UNIT_TURN_ANGLE</field>
  <value name="ROTATION">
    <shadow type="math_number">
      <field name="NUM">90</field>
    </shadow>
  </value>
  <value name="SPEED_SLIDER">
    <shadow type="math_number">
      <field name="NUM">75</field>
    </shadow>
  </value>
</block>

NAME_INPUT can be: "motor1", "motor2", "motor3", "motor4", "motor5", "motor6".
Use the following blocks to control the motors sequencially:

There is one button sensor, one distance sensor.



Prompt examples:



`


function AiRcView(){

  const SpeechRecognition = window.webkitSpeechRecognition;
  // if (typeof window['SpeechRecognition'] === 'undefined') {
  //   console.error('SpeechRecognition is not supported in this browser.');
  //   return <div>Speech Recognition is not supported in this browser.</div>;
  // }
  const recognition = new SpeechRecognition();
  recognition.lang = 'en-US';
  recognition.continuous = true; // or true for continuous listening
  recognition.interimResults = true;

  let editorRef!: HTMLDivElement;

  let lastXml = localStorage.getItem('ai-rc-code') || '';

  const [isListening, setIsListening] = createSignal(false);
  const [text, setText] = createSignal<string>('');

  onMount(() => {
    console.log('ai stub')
  });

  onCleanup(() => {
    console.log('ai stub exit')
  })

  const onSave = (code: string) => {
    // console.log('AI RC code saved:', code, arguments);
    localStorage.setItem('ai-rc-code', code);
    // setXml(code);
  }

  recognition.onresult = (event: any) => {
    let fullTranscript = '';
    for (let i = 0; i < event.results.length; i++) {
      fullTranscript += event.results[i][0].transcript + 'n';
    }
    console.log('Recognized:', fullTranscript);
    setText(fullTranscript);
    // setText(transcript);
  };


  createEffect(() => {
    if (isListening()) {
      console.log('AI RC listening started');
      recognition.start();
    }
    else {
      console.log('AI RC listening stopped');
      recognition.stop();
      // TODO: send it up to the GPT endpoint
      const code = text()
    }
  }, [isListening]);



  const [xml, setXml] = createSignal<string>(lastXml);


  return <div>
      <button class={styles.ai} classList={{[styles.listening]: isListening()}} onClick={() => {
        setIsListening(!isListening());
      }}>Robot Friend</button>
      <div>

      </div>
      {
        text() &&
        <div class={styles.prompt} innerHTML={text().replace(/n/g, '<br />')}></div> 
      }

    <BlocklyView onSave={onSave} xml={xml}></BlocklyView>
  </div>
}

export default AiRcView