import { programs } from "./Config";
import { log } from "./log";

const knightRiderLightsPython = `
robot.led.set(leds=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], color='#000000')
robot.play_tune('knight')
i = 0
while True:
  robot.led.set(leds=[i % 12 + 1], color='#FF0000')
  robot.led.set(leds=[(i - 1) % 12 + 1], color='#AA0000')
  robot.led.set(leds=[(i - 2) % 12 + 1], color='#330000')
  robot.led.set(leds=[(i - 3) % 12 + 1], color='#110000')
  robot.led.set(leds=[(i - 4) % 12 + 1], color='#000000')
  time.sleep(0.1)
  i += 1
`;

const keywords: { [keyword: string]: string } = {
  go: "drive",
  drive: "drive",
  turn: "turn",
  move: "drive",
  stop: "stop",

  rainbow: "rainbow",
  police: "police",

  blink: "blink",
  link: "blink",
  bring: "blink",
  drink: "blink",

  LEDs: "lights",
  light: "lights",
  lights: "lights",

  bark: "bark",
  dog: "bark",
  cat: "cat",
  meow: "cat",
  knight: "knight",
  night: "knight",
  kit: "knight",
};

const speedMap: { [keyword: string]: number } = {
  slow: 30,
  normal: 75,
  fast: 150,
};

const colors: { [keyword: string]: string } = {
  red: "#FF0000",
  green: "#00FF00",
  blue: "#0000FF",
  yellow: "#FFFF00",
  white: "#FFFFFF",
  orange: "#FFA500",
  purple: "#800080",
  pink: "#FFC0CB",
  cyan: "#00FFFF",
  magenta: "#FF00FF",
  gray: "#808080",
  brown: "#A52A2A",
  black: "#000000",
};

const directions: { [keyword: string]: string } = {
  left: "left",
  right: "right",
  front: "front",
  back: "back",
  around: "around",
};


let lastNumber: number | undefined;
let lastSpeed: string = "normal";
let lastDirection: string | undefined;
let lastMotorDirection: string = "Motor.DIRECTION_FWD";
let lastColor: string | undefined = "#FFFFFF"; // Default to white
let leds = "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]";

export const processVoiceCommandTranscript = (fullTranscript: string) => {
  // Find the last occurrence of any keyword by searching from the end of the string
  let lastCommand: string | undefined;
  let lastIndex = -1;
  let lastUnit = "cm";

  // Sometimes the transcript contains number words like "one", "two", etc.
  // We need to replace them with digits before processing
  // This is useful for commands like "drive one meter" or "turn two degrees"
  fullTranscript = replaceNumberWords(fullTranscript);

  const programMap: { [name: string]: string } = {};
  programs().map((p) => (programMap[p.name] = p.python));

  const keywordsWithPrograms = Object.assign({}, keywords, programMap);
  console.log(keywordsWithPrograms);

  for (const keyword of Object.keys(keywordsWithPrograms)) {
    const idx = fullTranscript.toLowerCase().lastIndexOf(keyword);
    if (idx > lastIndex && idx !== -1) {
      lastIndex = idx;
      lastCommand = keyword;

      const lastCommandText = fullTranscript.slice(idx + keyword.length);

      // Find any number after the keyword
      const numberMatch = lastCommandText.match(/(\d+)/);
      if (numberMatch) {
        lastNumber = parseInt(numberMatch[0]);
      }
      // Find any speed after the keyword
      const speedMatch = lastCommandText.match(/(slow|normal|fast)/);
      if (speedMatch) {
        lastSpeed = speedMatch[0];
      }

      const colorMatch = lastCommandText.match(
        /(red|green|blue|yellow|white|orange|purple|pink|cyan|magenta|gray|brown)/i
      );
      if (colorMatch) {
        const color = colors[colorMatch[0].toLowerCase()];
        lastColor = color || "#FFFFFF"; // Default to white if not found
      }
      const directionMatch = lastCommandText.match(
        /(left|right|front|back|forward|backward|around)/i
      );
      if (directionMatch) {
        const direction = directions[directionMatch[0].toLowerCase()];
        lastDirection = direction;
        switch (lastDirection) {
          case "left":
            leds = "[2, 3, 4]";
            lastDirection = "left";
            lastMotorDirection = "Motor.DIRECTION_LEFT";
            if (!numberMatch) {
              lastNumber = 90; // Default to 90 degrees if not specified
            }
            break;
          case "right":
            leds = "[8, 9, 10]";
            lastDirection = "right";
            lastMotorDirection = "Motor.DIRECTION_RIGHT";
            if (!numberMatch) {
              lastNumber = 90; // Default to 90 degrees if not specified
            }
            break;
          case "front":
          case "forward":
            leds = "[5, 6, 7]";
            lastDirection = "forward";
            lastMotorDirection = "Motor.DIRECTION_FWD";
            break;
          case "back":
          case "backward":
            leds = "[11, 12, 1]";
            lastDirection = "backward";
            lastMotorDirection = "Motor.DIRECTION_BACK";
            break;
          case "around":
            lastDirection = "around";
            lastMotorDirection = "Motor.DIRECTION_LEFT";
            lastNumber = 180;
          default:
            leds = "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]";
        }
        const unitMatch = lastCommandText.match(
          /(cm|centimeters|meter|meters| m|feet|foot|inch|inches)/i
        );
        if (unitMatch) {
          lastUnit = unitMatch[0].toLowerCase();
          if (lastUnit === "centimeters") {
            lastUnit = "cm"; // Convert centimeters to cm for consistency
          }
          if (
            lastUnit === "meter" ||
            lastUnit === "meters" ||
            lastUnit === " m"
          ) {
            lastUnit = "m"; // Convert degrees to turns for consistency
          } else if (lastUnit === "feet") {
            lastUnit = "cm"; // Convert feet/inches to centimeters
            if (lastNumber) {
              lastNumber *= 30.48; // Convert feet to cm
            }
          } else if (lastUnit === "inch") {
            lastUnit = "cm"; // Convert feet/inches to centimeters
            if (lastNumber) {
              lastNumber *= 2.54; // Convert inches to cm
            }
          } else {
            lastUnit = "cm"; // Default unit is cm
          }
        }
      }
    }
  }
  if (lastCommand) {
    const keyword = keywords[lastCommand];
    log(
      `Voice: ${keyword}(${lastCommand}): ${lastDirection}, ${lastNumber} ${lastUnit}, ${lastSpeed}, ${lastColor}`
    );

    if (lastCommand in programMap) {
      // If the command is a program name, return the program's Python code
      return programMap[lastCommand];
    }

    // Set the joystick position based on the detected command
    switch (keyword) {
      case "drive":
        if (
          ["Motor.DIRECTION_FWD", "Motor.DIRECTION_BACK"].indexOf(
            lastMotorDirection
          ) === -1
        ) {
          lastMotorDirection = "Motor.DIRECTION_FWD"; // Default to forward if not set
        }
        const multiplier = lastUnit === "m" ? 100 : 1; // Convert meters to centimeters

        if (lastNumber) {
          const dist = (lastNumber / 20) * multiplier;
          console.log(lastNumber, dist);
          // We assume CM, so calculate with this amount of turns:
          return `robot.drive(direction=${lastMotorDirection}, rotation=${dist}, unit_rotation=Motor.UNIT_ROT, speed=${speedMap[lastSpeed]}, unit_speed=Motor.UNIT_SPEED_RPM)`;
        } else {
          return `robot.drivetrain.set_speed(direction=${lastMotorDirection}, speed=${speedMap[lastSpeed]}, unit_speed=Motor.UNIT_SPEED_RPM)`;
        }

      case "turn":
        if (
          ["Motor.DIRECTION_LEFT", "Motor.DIRECTION_RIGHT"].indexOf(
            lastMotorDirection
          ) === -1
        ) {
          lastMotorDirection = "Motor.DIRECTION_LEFT"; // Default to forward if not set
        }
        // We assume degrees, but default is 90
        return `robot.turn(direction=${lastMotorDirection}, rotation=${
          lastNumber || 90
        }, unit_rotation=Motor.UNIT_TURN_ANGLE, speed=${
          speedMap[lastSpeed]
        }, unit_speed=Motor.UNIT_SPEED_RPM)`;

      case "stop":
        return `for motor in robot.motors: motor.stop(action=Motor.ACTION_RELEASE)`;

      case "blink":
        return `while True: time.sleep(0.4); robot.led.set(leds=${leds}, color='${lastColor}'); time.sleep(0.4); robot.led.set(leds=${leds}, color='#000000')`;
      case "lights":
        return `robot.led.set(leds=${leds}, color='${lastColor}')`;
      case "rainbow":
        return `robot.led.start_animation(RingLed.ColorWheel)`;
      case "police":
        return `robot.led.start_animation(RingLed.Siren)`;
      case "bark":
        return `robot.play_tune('dog')`;
      case "cat":
        return `robot.play_tune('cat')`;
      case "knight":
        return knightRiderLightsPython;
    }
  }
};


const numberWordsMap: { [word: string]: number } = {
  one: 1,
  two: 2,
  three: 3,
  four: 4,
  five: 5,
  six: 6,
  seven: 7,
  eight: 8,
  nine: 9,
  ten: 10,
  eleven: 11,
  twelve: 12,
  thirteen: 13,
  fourteen: 14,
  fifteen: 15,
  sixteen: 16,
  seventeen: 17,
  eighteen: 18,
  nineteen: 19,
  twenty: 20,
};

export function replaceNumberWords(text: string): string {
  return text.replace(
    new RegExp(`\\b(${Object.keys(numberWordsMap).join("|")})\\b`, "gi"),
    (match) => numberWordsMap[match.toLowerCase()].toString()
  );
}

// @ts-ignore
export const SpeechRecognition = window.webkitSpeechRecognition;
