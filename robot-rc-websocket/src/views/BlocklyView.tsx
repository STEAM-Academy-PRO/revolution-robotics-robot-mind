import { Accessor, createEffect, on, onMount } from "solid-js";
import { blocklyUrlBase } from "../settings";
import styles from './Blockly.module.css'

export function BlocklyView({onSave, xml}: {onSave: (code: string) => void, xml: Accessor<string>}) {

    let blocklyRef!: HTMLIFrameElement

    onMount(() => {
        console.log('BlocklyView mounted', blocklyRef);
        window.addEventListener('message', (event) => {
            if (event.data.type === 'save') {
                onSave(event.data.xml);
            }
        });
        blocklyRef.onload = () => {
            if (blocklyRef.contentWindow) {
                const x = xml()
                blocklyRef.contentWindow.postMessage({type: 'init', xml: x}, '*');
            } else {
                console.error('Blockly iframe contentWindow is not available');
            }
        }
    });

    createEffect(() => {
        const x = xml();
        console.log('BlocklyView xml changed:', x);
        if (x && blocklyRef?.contentWindow) {
            blocklyRef.contentWindow.postMessage({type: 'load', xml: x}, '*');
        }
    });

    return (
        <div>
            <iframe ref={blocklyRef} class={styles.blockly} src={`${blocklyUrlBase()}/interface.html`}></iframe>
        </div>
    )
}