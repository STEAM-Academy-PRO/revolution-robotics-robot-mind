import { createSignal, createEffect, Accessor, Setter, For, Show, createMemo } from 'solid-js'

import styles from './Config.module.css'

import { RobotMessage, SocketWrapper } from '../utils/Communicator';
import { uploadConfig } from '../utils/commands';
import { BlocklyItem, DriveMode, RobotConfig, Sensor } from '../utils/Config';
import CodeEditor from './CodeEditor';


function CodeView({
  config, setConfig,
  conn
}: { config: Accessor<RobotConfig>, setConfig: Setter<RobotConfig>, conn: Accessor<SocketWrapper | null> }) {

  const [isSendEnabled, setIsSendEnabled] = createSignal(false);
  const [edited, setEdited] = createSignal<BlocklyItem | null>(null)
  const [editedCode, setEditedCode] = createSignal<string>('')
  const [configString, setConfigString] = createSignal<string>('');
  const [editedIndex, setEditedIndex] = createSignal<number | null>(null);
  const [driveMode, setDriveMode] = createSignal<DriveMode>(DriveMode.drive_joystick)


  createEffect(() => {
    try {
      setIsSendEnabled(Boolean(conn()))
    } catch (e) {
      setIsSendEnabled(false)
    }
  });

  const handleSend = () => {
    uploadConfig(conn(), config())
    conn()?.send(RobotMessage.configure, JSON.stringify(config()))
  }

  const saveCode = () => {
    const newConfig = Object.assign({}, config()) as RobotConfig
    const editedCodeBlock = edited()
    if (editedCodeBlock) {
      editedCodeBlock.pythoncode = btoa(editedCode())
    }
    setConfig(newConfig)
  }

  const updateConfigString = (e: Event) => setConfigString((e.target as HTMLTextAreaElement).value || '')

  // function tabHandler (e: KeyboardEvent) {
  //   const textarea = this
  //   if (e.key === 'Tab') {
  //     e.preventDefault(); // Prevent the default tab behavior (focus change)
  //     const start = textarea.selectionStart;
  //     const end = textarea.selectionEnd;

  //     // Set the value of the textarea to: text before caret + tab + text after caret
  //     textarea.value = textarea.value.substring(0, start) + '\t' + textarea.value.substring(end);

  //     // Move the caret to the right of the inserted tab
  //     textarea.selectionStart = textarea.selectionEnd = start + 1;
  //   }
  // }

  createEffect(() => setEditedCode(atob(edited()?.pythoncode || '')))

  let editor

  return (
    <div >
      <div class={styles.controller}>
        <div class={styles.column}>
          <div>

            <h4>Button Bindings</h4>
            <For each={config().blocklyList.filter((c) => !c.builtinScriptName)}>{(script, i) =>
              <div class={styles.clickable} classList={{ [styles.active]: editedIndex() === i() }} onClick={() => {
                setEdited(null)
                setEdited(script)
                setEditedIndex(i)
                setConfigString('')
              }}>{String(i())}</div>
            }</For>

            <p>
              <Show when={edited() !== null}>
                <button onClick={() => saveCode()}>SAVE CODE</button>
              </Show>
            </p>

            <p>
              <Show when={!configString()}>
                <button onClick={() => {setConfigString(JSON.stringify(config(), null, 2)); setEdited(null)}}>RAW config</button>
              </Show>
            </p>

            <p>
              <button onClick={handleSend} disabled={!isSendEnabled()}>Send</button>
            </p>

          </div>

        </div>
        <div class={styles.editor}></div>
        <Show when={edited() !== null}>
          {/* <h3>Edit Python Code for button {editedIndex()}</h3> */}
          {/* <textarea value={editedCode()} onchange={(e) => setEditedCode(e.target.value)} onKeyDown={tabHandler}></textarea> */}
          <CodeEditor value={editedCode} setValue={setEditedCode}></CodeEditor>
        </Show>

        <Show when={configString()}>
          <textarea value={configString()}
            onChange={updateConfigString}
            onKeyUp={updateConfigString}
            ></textarea>
            <div ref={editor}></div>
        </Show>


      </div>

      {/* <pre class={styles.pre} onClick={() => setConfigString(JSON.stringify(config() || ''))}>
        {JSON.stringify(config(), null, 2)}
      </pre> */}
      {/* {response() && (
        <div>
          <h2>Response</h2>
          <pre>{JSON.stringify(response(), null, 2)}</pre>
        </div>
      )} */}
    </div>
  );
}

export default CodeView;
