
export enum DriveMode {
    drive_joystick = 'drive_joystick',
    drive_2sticks = 'drive_2sticks'
}

export interface BlocklyItem {
    assignments: {
        analog?: {
            channels: number[]
            priority: number
        },
        buttons?: { id: number, priority: number }[]
        variableSlots?: string[]
    },
    builtinScriptName?: DriveMode
    pythoncode?: string
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


export interface RobotConfig {
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

export interface Sensor {
    name: string
    type: number
}