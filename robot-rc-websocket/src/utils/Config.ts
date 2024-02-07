
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

interface SensorConfig { }

interface MotorConfig {
    reversed: number // 0 1
    name: string // motor1 - motor6
    type: number // default 2 ???
    side: number // used by the joystick script I assume
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