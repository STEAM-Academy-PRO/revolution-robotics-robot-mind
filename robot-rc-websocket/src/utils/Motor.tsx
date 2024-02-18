import { Show, createEffect, createSignal } from "solid-js";
import { MotorConfig, MotorReversed, MotorSide, MotorType } from "./Config";

import styles from '../views/Config.module.css'

export function MotorView({motor, update}: {motor: MotorConfig, update: (motor: MotorConfig)=>void}){

    const [reversed, setReversed] = createSignal<number>(motor.reversed)
    const [type, setType] = createSignal<number>(motor.type)
    const [side, setSide] = createSignal<number>(motor.side)

    let inited = false
    createEffect(()=>{
        motor.reversed = reversed()
        motor.type = type()
        motor.side = side()
        if (inited){
            update(motor)
        } else {
            inited = true
        }
        
    })

    return <div>
        <div>
            {motor.name}
        </div>
        <div>
            <a class={styles.clickable}
                classList={{ [styles.bold]: type() === MotorType.MOTOR}}
                onClick={()=>
                    setType(MotorType.MOTOR)}>
            MOTOR </a>
            <a class={styles.clickable}
                classList={{ [styles.bold]: type() === MotorType.DRIVE}}
                onClick={()=>
                setType(MotorType.DRIVE)
            }>DRIVE</a>
        </div>
        <Show when={type() === MotorType.DRIVE}>
            <div>
                <a class={styles.clickable}
                    classList={{ [styles.bold]: side() === MotorSide.LEFT}}
                    onClick={()=>
                        setSide(MotorSide.LEFT)}>
                left </a>
                <a class={styles.clickable}
                    classList={{ [styles.bold]: side() === MotorSide.RIGHT}}
                    onClick={()=>
                    setSide(MotorSide.RIGHT)
                }>right</a>
            </div>
            <div>
                <a class={styles.clickable}
                    classList={{ [styles.bold]: reversed() === MotorReversed.TRUE}}
                    onClick={()=>
                        setReversed(MotorReversed.TRUE)}>
                yes </a>
                <a class={styles.clickable}
                    classList={{ [styles.bold]: reversed() ===  MotorReversed.FALSE}}
                    onClick={()=>
                        setReversed(MotorReversed.FALSE)
                }>no</a>
            </div>
        </Show>
    </div>
}