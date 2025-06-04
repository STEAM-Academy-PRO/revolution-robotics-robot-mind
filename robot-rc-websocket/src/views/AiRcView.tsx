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

There is max one button sensor and max one distance sensor, and a built in direction sensor (IMU) that can be used to read the robot's orientation.

There are the following blocks to interact with them:
Read their number value:
<block type=\"block_ultrasonic_sensor\"></block>

Returns boolean true/false if the distance is less than 20 cm:
<block type="block_is_object_near"></block>

Button is pressed (returns boolean true/false)
<block type="block_bumper"></block>

Check IMU orientation (360 degrees for full circle):
<block type=\"block_gyroscope_sensor\"></block>


Make the program wait for a given number of seconds (can be float):

<block type=\"block_wait\">
  <value name=\"WAIT\">
    <shadow type=\"math_number\">
      <field name=\"NUM\">1</field>
    </shadow>
  </value>
</block>


The following control blocks are available:

If-then:
<block type="if_then">
  <value name="COND">
    ... binary condition to check (blocks) ...
  </value>
  <statement name="IN_IF">
    ... blocks to execute if condition is true ...
  </statement>
</block>


If-then-else:
<block type="if_then_else">
  <value name="COND">
    ... binary condition to check (blocks) ...
  </value>
  <statement name="IN_IF">
    ... blocks to execute if condition is true ...
  </statement>
  <statement name="IN_ELSE">
    ... blocks to execute if condition is false ...
  </statement>
</block>

Loop with front condition:
<block type=\"block_repeat_while\"></block>
  <value name="CONDITION">
    ... binary condition to check (blocks) ...
  </value>
  <statement name="STATEMENT">
    ... blocks within the loop ...
  </statement>
</block>

Repeat a number of times:
<block type="controls_repeat_ext2">
  <value name="TIMES">
    <shadow type="math_number">
      <field name="NUM">3</field>
    </shadow>
  </value>
  <statement name="DO">
    ... blocks to repeat ...
  </statement>
</block>

You can break loop boxes with:
<block type="block_break"></block>


The following logic blocks are available:

<block type="logic_and">
  <value name="LEFT">
    <shadow type="logic_boolean">
      <field name="BOOL">TRUE</field>
    </shadow>
  </value>
  <value name="RIGHT">
    <shadow type="logic_boolean">
      <field name="BOOL">TRUE</field>
    </shadow>
  </value>
</block>

<block type="logic_or">
  <value name="LEFT">
    <shadow type="logic_boolean">
      <field name="BOOL">TRUE</field>
    </shadow>
  </value>
  <value name="RIGHT">
    <shadow type="logic_boolean">
      <field name="BOOL">TRUE</field>
    </shadow>
  </value>
</block>

Returns a boolean value:
LOGIC_SELECTOR values: EQ, NEQ, GT, GTE, LT, LTE

<block type="logic_compare2">
  <field name="LOGIC_SELECTOR">NEQ</field>
  <value name="A">
    <block type="math_number">
      <field name="NUM">0</field>
    </block>
  </value>
  <value name="B">
    <shadow type="math_number">
      <field name="NUM">10</field>
    </shadow>
  </value>
</block>

Negate a boolean value:
<block type="logic_not">
  <value name="RIGHT">
    <shadow type="logic_boolean">
      <field name="BOOL">TRUE</field>
    </shadow>
  </value>
</block>

Math blocks:
OPERATOR_SELECTOR values: ADD, MINUS, MULTIPLY, DIVIDE, MODULO
<block type="math_arithmetic2">
  <field name="OPERATOR_SELECTOR">ADD</field>
  <value name="A">
    <shadow type="math_number">
      <field name="NUM">0</field>
    </shadow>
  </value>
  <value name="B">
    <shadow type="math_number">
      <field name="NUM">0</field>
    </shadow>
  </value>
</block>

Rounding numbers:
OPERATOR_SELECTOR values: ROUND, ROUNDUP, ROUNDDOWN
<block type="math_round2">
  <field name="OPERATOR_SELECTOR">ROUND</field>
  <value name="NUM">
    <shadow type="math_number">
      <field name="NUM">0</field>
    </shadow>
  </value>
</block>

Trigonometry:
MATH_TRIG_SELECTOR values: sin, cos, tan
<block type="math_trig2">
  <field name="MATH_TRIG_SELECTOR">sin</field>
  <value name="RIGHT">
    <shadow type="math_number">
      <field name="NUM">0</field>
    </shadow>
  </value>
</block>

Special value numbers:
<block type="math_pi"></block>


On the robot there is a circular LED ring that can be controlled with the following blocks:
LEDs are indexed from 1 to 12, starting from the top and going clockwise.

<block type="block_set_all_leds">
  <value name="COLOR">
    <shadow type="colour_picker">
      <field name="COLOUR">#ffcc00</field>
    </shadow>
  </value>
</block>

<block type="block_set_multiple_led">
  <field name="LED_IDS">1,2,3</field>
  <value name="COLOR">
    <shadow type="colour_picker">
      <field name="COLOUR">#ff0000</field>
    </shadow>
  </value>
</block>

<block type="block_set_led">
  <value name="LED">
    <shadow type="math_number">
      <field name="NUM">1</field>
    </shadow>
  </value>
  <value name="COLOR">
    <shadow type="colour_picker">
      <field name="COLOUR">#ff0000</field>
    </shadow>
  </value>
</block>

Switch all LEDs off:
<block type="block_set_leds_black_small"></block>

Variables should be declared at the top of all blocks, inside the XML main tag like this:
<variables>
  <variable>asfd</variable>
</variables>

Then use them like this:
<block type="variables_get">
  <field name="VAR">asfd</field>
</block>

<block type="variables_set">
  <field name="VAR">variable1</field>
  <value name="VALUE">
    <shadow type="math_number">
      <field name="NUM">1</field>
    </shadow>
  </value>
</block>


Prompt examples:

Repeat 4 times so we arrive at the same spot:
Drive forward for 30 cm, then turn left 90 degrees

<xml xmlns="https://developers.google.com/blockly/xml">
  <block type="block_start">
    <next>
      <block type="controls_repeat_ext2">
        <value name="TIMES">
          <shadow type="math_number">
            <field name="NUM">4</field>
          </shadow>
        </value>
        <statement name="DO">
          <block type="block_drive">
            <field name="DIRECTION_SELECTOR">Motor.DIRECTION_FWD</field>
            <field name="UNIT_ROTATION_SELECTOR">Motor.UNIT_ROT</field>
            <field name="UNIT_SPEED_SELECTOR">Motor.UNIT_SPEED_RPM</field>
            <value name="ROTATION">
              <shadow type="math_number">
                <field name="NUM">5</field>
              </shadow>
            </value>
            <value name="SPEED_SLIDER">
              <shadow type="math_number">
                <field name="NUM">75</field>
              </shadow>
            </value>
            <next>
              <block type="block_turn">
                <field name="DIRECTION_SELECTOR">Motor.DIRECTION_RIGHT</field>
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
            </next>
          </block>
        </statement>
      </block>
    </next>
  </block>
</xml>


Compass: always point the LED ring to one direction.

<xml xmlns="https://developers.google.com/blockly/xml">
  <variables>
    <variable>lastled</variable>
  </variables>
  <block type="block_start">
    <next>
      <block type="block_set_leds_black_small">
        <next>
          <block type="variables_set">
            <field name="VAR">lastled</field>
            <value name="VALUE">
              <shadow type="math_number">
                <field name="NUM">1</field>
              </shadow>
            </value>
            <next>
              <block type="block_repeat_while">
                <value name="CONDITION">
                  <block type="logic_boolean">
                    <field name="BOOL">TRUE</field>
                  </block>
                </value>
                <statement name="STATEMENT">
                  <block type="block_set_led">
                    <value name="LED">
                      <shadow type="math_number">
                        <field name="NUM">1</field>
                      </shadow>
                      <block type="variables_get">
                        <field name="VAR">lastled</field>
                      </block>
                    </value>
                    <value name="COLOR">
                      <shadow type="colour_picker">
                        <field name="COLOUR">#000000</field>
                      </shadow>
                    </value>
                    <next>
                      <block type="variables_set">
                        <field name="VAR">lastled</field>
                        <value name="VALUE">
                          <shadow type="math_number">
                            <field name="NUM">1</field>
                          </shadow>
                          <block type="math_arithmetic2">
                            <field name="OPERATOR_SELECTOR">MULTIPLY</field>
                            <value name="A">
                              <shadow type="math_number">
                                <field name="NUM">0</field>
                              </shadow>
                              <block type="math_arithmetic2">
                                <field name="OPERATOR_SELECTOR">DIVIDE</field>
                                <value name="A">
                                  <shadow type="math_number">
                                    <field name="NUM">0</field>
                                  </shadow>
                                  <block type="block_gyroscope_sensor"></block>
                                </value>
                                <value name="B">
                                  <shadow type="math_number">
                                    <field name="NUM">360</field>
                                  </shadow>
                                </value>
                              </block>
                            </value>
                            <value name="B">
                              <shadow type="math_number">
                                <field name="NUM">-12</field>
                              </shadow>
                            </value>
                          </block>
                        </value>
                        <next>
                          <block type="block_set_led">
                            <value name="LED">
                              <shadow type="math_number">
                                <field name="NUM">1</field>
                              </shadow>
                              <block type="variables_get">
                                <field name="VAR">lastled</field>
                              </block>
                            </value>
                            <value name="COLOR">
                              <shadow type="colour_picker">
                                <field name="COLOUR">#3366ff</field>
                              </shadow>
                            </value>
                          </block>
                        </next>
                      </block>
                    </next>
                  </block>
                </statement>
              </block>
            </next>
          </block>
        </next>
      </block>
    </next>
  </block>
</xml>





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