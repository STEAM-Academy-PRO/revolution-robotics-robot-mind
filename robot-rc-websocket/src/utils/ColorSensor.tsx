import { Accessor, Show, createEffect, createSignal } from "solid-js"
import styles from '../views/Controller.module.css'

export function ColorSensor({ value }: { value: Accessor<ColorSensorReading> }) {

    const [top, setTop] = createSignal<Color>({ r: 0, g: 0, b: 0 })
    const [right, setRight] = createSignal<Color>({ r: 0, g: 0, b: 0 })
    const [left, setLeft] = createSignal<Color>({ r: 0, g: 0, b: 0 })
    const [middle, setMiddle] = createSignal<Color>({ r: 0, g: 0, b: 0 })

    createEffect(() => {
        if (!value()) return
        setTop(value().top)
        setRight(value().right)
        setLeft(value().left)
        setMiddle(value().middle)
    })

    return <div>
        <Show when={value()}>
            <table style={styles.colorSensorTable}>
                <tbody>
                    <tr><td colspan="3"><ColorSquare color={top} /></td></tr>
                    <tr>
                        <td><ColorSquare color={left} /></td>
                        <td><ColorSquare color={middle} /></td>
                        <td><ColorSquare color={right} /></td>
                    </tr>
                </tbody>
            </table>
        </Show>
    </div>
}

function ColorSquare({ color }: { color: Accessor<Color> }) {
    return <span class={styles.colorBox}
        style={{ "background-color": `rgb(${color().r}, ${color().g}, ${color().b}` }}
        title={JSON.stringify(color)}></span>
}

export interface ColorSensorReading {
    top: Color
    right: Color
    left: Color
    middle: Color

}

export interface Color {
    r: number
    g: number
    b: number
}
