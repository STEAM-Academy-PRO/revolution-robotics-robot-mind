import { Accessor, createEffect, on, onMount } from "solid-js";
import { blocklyUrlBase } from "../settings";
import styles from './Blockly.module.css'

export function BlocklyView({onSave, xml, reloadCode}: {
    onSave: (xml: string, python: string) => void, 
    xml: string | Accessor<string>,
    reloadCode?: (code: string) => void
}) {

    let blocklyRef!: HTMLIFrameElement
    let xmlString = typeof xml === 'function' ? xml() : xml;
    let oncePerLoad = false

    onMount(() => {
        // console.log('BlocklyView mounted', blocklyRef);
        let debounceTimeout: number | undefined;
        window.addEventListener('message', (event) => {
            if (event.data.type === 'save') {
                if (oncePerLoad) {
                    oncePerLoad = false; // Reset after first load
                    reloadCode?.(event.data.python);
                }
            if (debounceTimeout) clearTimeout(debounceTimeout);
            debounceTimeout = window.setTimeout(() => {
                onSave(event.data.xml, event.data.python);
            }, 300); // 300ms debounce
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
        // console.log('BlocklyView xml changed:', xmlString);
        if (xmlString && blocklyRef?.contentWindow) {
            oncePerLoad = true; // Prevents multiple loads
            blocklyRef.contentWindow.postMessage({type: 'load', xml: xmlString}, '*');
        }
    });

    return (
        <div>
            <iframe ref={blocklyRef} class={styles.blockly} src={`${blocklyUrlBase()}/interface.html`}></iframe>
        </div>
    )
}