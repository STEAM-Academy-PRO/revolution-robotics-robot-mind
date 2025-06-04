import { Accessor, createEffect, on, onMount } from "solid-js";
import { blocklyUrlBase } from "../settings";
import styles from './Blockly.module.css'

export function BlocklyView({onSave, xml}: {onSave: (xml: string, python: string) => void, xml: string | Accessor<string>}) {

    let blocklyRef!: HTMLIFrameElement
    let xmlString = typeof xml === 'function' ? xml() : xml;

    onMount(() => {
        console.log('BlocklyView mounted', blocklyRef);
        window.addEventListener('message', (event) => {
            if (event.data.type === 'save') {
                onSave(event.data.xml, event.data.python);
            }
        });
        blocklyRef.onload = () => {
            if (blocklyRef.contentWindow) {
                const x = xmlString
                blocklyRef.contentWindow.postMessage({type: 'init', xml: x}, '*');
            } else {
                console.error('Blockly iframe contentWindow is not available');
            }
        }
    });

    createEffect(() => {
        let xmlString = typeof xml === 'function' ? xml() : xml;
        console.log('BlocklyView xml changed:', xmlString);
        if (xmlString && blocklyRef?.contentWindow) {
            blocklyRef.contentWindow.postMessage({type: 'load', xml: xmlString}, '*');
        }
    });

    return (
        <div>
            <iframe ref={blocklyRef} class={styles.blockly} src={`${blocklyUrlBase()}/interface.html`}></iframe>
        </div>
    )
}