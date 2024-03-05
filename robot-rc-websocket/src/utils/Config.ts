
import DEFAULT_V1_JSON from "../assets/robot-config.json"

import { createEffect, createSignal } from "solid-js"
import { uploadConfig } from "./commands"
import { RobotMessage } from "./Communicator"
import { conn } from "../settings"
import { python } from "@codemirror/lang-python"

export enum DriveMode {
    drive_joystick = 'drive_joystick',
    drive_2sticks = 'drive_2sticks',
    custom = 'custom'
}

// Load default config as fallback.
let defaultConfig: RobotConfigV1 = DEFAULT_V1_JSON as RobotConfigV1

// If there is a config in local storage, use that instead.
try { defaultConfig = JSON.parse(localStorage.getItem('config') || '') as RobotConfigV1 || DEFAULT_V1_JSON } catch (e) { }
const programStoreRaw = localStorage.getItem('programs')
const programsFromCache = programStoreRaw ? JSON.parse(programStoreRaw) : []

const buttonBindingsRaw = localStorage.getItem('buttonBindings')
const buttonBindingsCache = buttonBindingsRaw ? JSON.parse(buttonBindingsRaw) : {}

const savedDriveMode = localStorage.getItem('driveMode')
const driveModeFromCache = savedDriveMode ? savedDriveMode as DriveMode : DriveMode.drive_joystick

export const [currentConfig, setCurrentConfig] = createSignal<RobotConfigV1>(defaultConfig)
export const [sensors, setSensors] = createSignal<Array<SensorConfig | null>>(currentConfig().robotConfig.sensors)
export const [motors, setMotors] = createSignal<Array<MotorConfig | null>>(currentConfig().robotConfig.motors)
export const [driveMode, setDriveMode] = createSignal<DriveMode>(driveModeFromCache)



export const [programs, setPrograms] = createSignal<Array<Program>>(programsFromCache)
export const [scriptBindings, setScriptBindings] = createSignal<{ [name: string]: string }>(buttonBindingsCache)

// Buttons, and now the analog value.
export const scriptBindingTargets = [
    'drive',
    'button_up',
    'button_right',
    'button_down',
    'button_left'
  ]

let prevConfig = currentConfig()

createEffect(() => {
    driveMode()
    motors()
    sensors()
    scriptBindings()
    programs()
    const conf = Object.assign({}, prevConfig)
    conf.robotConfig.motors = motors()
    conf.robotConfig.sensors = sensors()

    conf.blocklyList = buildBlocklyItems()

    // Autosave on change
    setCurrentConfig(conf)
    console.warn('saving config', conf)

    localStorage.setItem('config', JSON.stringify(conf));
    localStorage.setItem('programs', JSON.stringify(programs()))
    localStorage.setItem('buttonBindings', JSON.stringify(scriptBindings()))
    localStorage.setItem('driveMode', driveMode())

    prevConfig = conf

    return conf
})

function buildBlocklyItems(){
    const ret: Array<BlocklyItem> = []
    Object.keys(scriptBindings()).forEach((key) => {
        const pythonCodeBase64 = btoa(programs().find((p) => p.name === scriptBindings()[key])?.code || '')

        if (key === 'drive') {
            ret.push(createPredefinedDriveBlocklyItem(driveMode(), pythonCodeBase64))
        } else {
            ret.push({
                assignments: {
                    buttons: [{
                        id: scriptBindingTargets.indexOf(key),
                        priority: 0
                    }]
                },
                pythoncode: btoa(pythonCodeBase64)
            })
        }
    })
    return ret
}

export function handleSend() {

    uploadConfig(conn(), currentConfig())
    conn()?.send(RobotMessage.configure, JSON.stringify(currentConfig(), null, 2))
}


export const handleDriveChange = (event: Event) => {
    const target = event.target as HTMLSelectElement;
    setDriveMode(target.value as DriveMode);
}



export interface BlocklyItem {
    assignments: {
        analog?: [{
            channels: number[]
            priority: number
        }],
        buttons?: { id: number, priority: number }[]
        variableSlots?: string[]
    },
    builtinScriptName?: DriveMode
    pythoncode?: string
}

function createPredefinedDriveBlocklyItem(mode: DriveMode, pythonCode: string): BlocklyItem {
    const ret: BlocklyItem = {
        assignments: {
            analog: [{
                channels: [0, 1],
                priority: 0
            }]
        }
    }
    // Custom drive mode.
    if (mode === DriveMode.custom) {
        if (!ret.assignments.analog) throw new Error(); // make the linter happy.
        ret.assignments.analog[0].channels = [0, 1, 2, 3]
        ret.pythoncode = pythonCode
    } else {
        ret.builtinScriptName = mode
    }
    return ret
}

export interface SensorConfig {
    name: string
    type: SensorType
}

export enum SensorType {
    COLOR = 4,
    DISTANCE = 1,
    BUTTON = 2
}

export const SensorTypeResolve = {
    4: 'color_sensor',
    1: 'distance_sensor',
    2: 'button'
}

export interface MotorConfig {
    reversed: number // 0 1
    name: string // motor1 - motor6
    type: number // type: 1: motor, drive: 2 ???
    side: number // used by the joystick script I assume
}
export enum MotorType {
    MOTOR = 1,
    DRIVE = 2
}
export enum MotorSide {
    LEFT = 0,
    RIGHT = 1
}

export enum MotorReversed {
    TRUE = 1,
    FALSE = 0
}


export interface RobotConfigV1 {
    blocklyList: Array<BlocklyItem>
    robotConfig: {
        sensors: SensorConfig[]
        motors: MotorConfig[]
    }

}

const Sensors = [{
    "name": "distance_sensor",
    "type": 1
},
{
    "name": "button",
    "type": 2
},
{
    "name": "color_sensor",
    "type": 4
}]

export interface Program {
    name: string,
    code: string,
    blocklyXml?: string
}

export interface Sensor {
    name: string
    type: number
}