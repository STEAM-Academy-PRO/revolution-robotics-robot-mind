import { blocklyUrlBase } from "../settings";
import styles from './Blockly.module.css'

export function BlocklyView({onSave}: {onSave: (code: string) => void}){
    return (
        <div>
            <iframe class={styles.blockly} src={`${blocklyUrlBase()}/desktop.html`}></iframe>
        </div>
    )
}