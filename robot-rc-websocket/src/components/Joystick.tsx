import { Position } from "../utils/Position";
import { Accessor, createEffect, onCleanup, onMount } from "solid-js"
import { clamp } from "../utils/mapping";
import styles from "./Joystick.module.css"

export function Joystick({ position, enabled }: 
    { position: Position, enabled: Accessor<boolean> }) {

    let canvasCtx: CanvasRenderingContext2D | null
    let canvas: HTMLCanvasElement;
    onMount(() => {
        canvasCtx = canvas?.getContext("2d");
        canvas.addEventListener('mousedown', handleStart);
        canvas.addEventListener('touchstart', handleStart, { passive: false });
    })


    // Function to update joystick position based on mouse event
    const updatePosition = (event: Event) => {
        if (!enabled()){ return }
        let clientX: number = 0;
        let clientY: number = 0;

        if ('touches' in event) {
            const touch = (event as TouchEvent).touches[0];
            if (touch) {
                clientX = touch.clientX;
                clientY = touch.clientY;
            }
        } else {
            clientX = (event as MouseEvent).clientX;
            clientY = (event as MouseEvent).clientY;
        }

        const rect = canvas.getBoundingClientRect();
        const offsetX = clientX - rect.left;
        const offsetY = clientY - rect.top;
        // Normalize the position to be between -1 and 1
        const normalizedX = (offsetX / rect.width) * 2 - 1;
        const normalizedY = (offsetY / rect.height) * 2 - 1;

        // Limit the joystick position to stay within the circle
        const magnitude = Math.sqrt(normalizedX ** 2 + normalizedY ** 2);
        const limitedMagnitude = Math.min(magnitude, 0.78);
        const limitedX = normalizedX / magnitude * limitedMagnitude;
        const limitedY = normalizedY / magnitude * limitedMagnitude;

        // Update signals
        position.setX(clamp(limitedX, -1, 1));
        position.setY(clamp(-limitedY, -1, 1)); // Invert Y to match typical coordinate systems
    };

    createEffect(() => {
        if (canvasCtx) {
            canvasCtx.clearRect(0, 0, 200, 200);
            canvasCtx.fillStyle = '#3498db';
            canvasCtx.beginPath();
            canvasCtx.arc(100 + position.x() * 100, 100 - position.y() * 100, 20, 0, 2 * Math.PI);
            canvasCtx.fill();
        }
    })

    const reset = () => { position.setX(0); position.setY(0) }

    onCleanup(() => {
        document.removeEventListener('mousemove', handleMove);
        document.removeEventListener('touchmove', handleMove);
        document.removeEventListener('mouseup', handleEnd);
        document.removeEventListener('touchend', handleEnd);
    });

    const handleStart = (event: Event) => {
        event.preventDefault(); // Prevent default behavior for touch events
        updatePosition(event);
        document.addEventListener('mousemove', handleMove);
        document.addEventListener('touchmove', handleMove, { passive: false });
        document.addEventListener('mouseup', handleEnd);
        document.addEventListener('touchend', handleEnd);
    };

    const handleMove = (event: Event) => {
        event.preventDefault(); // Prevent default behavior for touch events
        updatePosition(event);
    };

    const handleEnd = () => {
        document.removeEventListener('mousemove', handleMove);
        document.removeEventListener('touchmove', handleMove);
        document.removeEventListener('mouseup', handleEnd);
        document.removeEventListener('touchend', handleEnd);
        position.setX(0)
        position.setY(0)
    };

    return <canvas
        width="200"
        height="200"
        class={styles.joystickCanvas}
        classList={{[styles.joystickCanvasEnabled]: enabled()}}
        ref={canvas!}
    ></canvas>

}
