import { For, Show, createEffect, createMemo, createSignal } from "solid-js";
import styles from './log.module.css'

const [_log, setLog] = createSignal<Array<{ level: LogLevel, msg: string, time: string }>>([]);

export enum LogLevel {
  INFO = "INFO",
  ERROR = "ERROR",
  WARN = "WARN"
};

export const log = (msg: any, level: LogLevel = LogLevel.INFO) => {
  if (!msg) return;

  const newList = _log().slice()
  newList.push({
    level,
    msg,
    time: new Date().toLocaleTimeString("en-US", { hour12: false })
  })
  console.error(msg)
  setLog(newList);
}

export function Log() {
  let logElement: HTMLDivElement;
  createEffect(() => {
    _log()
    console.warn('changed', _log())
    if (logElement) {
      logElement.scrollTop = logElement.scrollHeight
    }
  })

  return <div>
    <Show when={_log().length}>
      <button onClick={() => clearLog()}>clear</button>
    </Show>
    <div ref={logElement!} class={styles.log}>
      <For each={_log()}>{(entry) =>
        <div classList={{
          [styles.info]: entry.level === LogLevel.INFO,
          [styles.error]: entry.level === LogLevel.ERROR,
          [styles.warn]: entry.level === LogLevel.WARN
        }}>
          <span class={styles.time}>[{entry.time}] </span>
          <span>{entry.msg.split('\n').length > 1 ?
            entry.msg.split('\n').map(e=><div>{e}</div>):entry.msg
            }
            </span>
        </div>
      }
      </For>
    </div>
  </div>
}

export const clearLog = () => {
  setLog([])
}