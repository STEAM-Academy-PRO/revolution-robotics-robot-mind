import { createEffect, createSignal } from "solid-js";
import { SensorConfig, SensorType, SensorTypeResolve } from "./Config";

import styles from '../views/Config.module.css'

export function SensorView({sensor, update}: {sensor: SensorConfig, update: (sensor: SensorConfig)=>void}){

    const [type, setType] = createSignal<number>(sensor.type)

    let inited = false
    createEffect(()=>{
        sensor.type = type()
        sensor.name = SensorTypeResolve[type()]
        if (inited){
            update(sensor)
        } else {
            inited = true
        }
    })

    return <div>
        <div>
            {sensor.name}
        </div>
        <div>
            <a class={styles.clickable}
                classList={{ [styles.bold]: type() === SensorType.BUTTON}}
                onClick={()=>
                    setType(SensorType.BUTTON)}>
            BUTTON </a>
            <a class={styles.clickable}
                classList={{ [styles.bold]: type() === SensorType.DISTANCE}}
                onClick={()=>
                setType(SensorType.DISTANCE)
            }>DISTANCE</a>
            <a class={styles.clickable}
                classList={{ [styles.bold]: type() === SensorType.COLOR}}
                onClick={()=>
                setType(SensorType.COLOR)
            }>COLOR</a>
        </div>
    </div>
}