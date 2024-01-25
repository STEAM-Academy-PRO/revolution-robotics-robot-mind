import { Accessor, Setter, createSignal } from "solid-js";

export class Position {
    x: Accessor<number>
    y: Accessor<number>
    setX: Setter<number>
    setY: Setter<number>
    constructor() {
        const [x, setX] = createSignal<number>(0);
        const [y, setY] = createSignal<number>(0);
        this.x = x
        this.y = y
        this.setX = setX
        this.setY = setY
    }
}