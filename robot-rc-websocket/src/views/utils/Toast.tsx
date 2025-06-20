import { Accessor, createEffect, createSignal, onCleanup, Show } from "solid-js";
import styles from "./Toast.module.css";

type ToastProps = {
    message: Accessor<string>;
    timeout?: Accessor<number>; // in milliseconds
};

export function Toast(props: ToastProps) {
    const [visible, setVisible] = createSignal(true);

    let timer = setTimeout(() => setVisible(false), props.timeout?.() ?? 3000);
    createEffect(() => {
        setVisible(Boolean(props.message()))
        if (timer) {
            clearTimeout(timer);
        }
        timer = setTimeout(() => setVisible(false), props.timeout?.() ?? 3000);
    });

    onCleanup(() => clearTimeout(timer));

    return (
        <Show when={visible()}>
            <div
                class={styles.toast}
            >
                {props.message()}
            </div>
        </Show>
    );
}