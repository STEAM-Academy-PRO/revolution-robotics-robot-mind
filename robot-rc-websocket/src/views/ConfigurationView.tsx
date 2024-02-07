import { createSignal, createEffect, Accessor, Setter, For, Show, createMemo } from 'solid-js'

import styles from './Config.module.css'

import { RobotMessage, SocketWrapper } from '../utils/Communicator';
import { uploadConfig } from '../utils/commands';
import { BlocklyItem, DriveMode, RobotConfig, Sensor } from '../utils/Config';

function ConfigurationView({
  config, setConfig,
  conn
}: { config: Accessor<RobotConfig>, setConfig: Setter<RobotConfig>, conn: Accessor<SocketWrapper | null> }) {

  const [isSendEnabled, setIsSendEnabled] = createSignal(false);
  const [edited, setEdited] = createSignal<BlocklyItem | null>(null)
  const [editedCode, setEditedCode] = createSignal<string>('')
  const [configString, setConfigString] = createSignal<string>('');
  const [editedIndex, setEditedIndex] = createSignal<number | null>(null);
  const [driveMode, setDriveMode] = createSignal<DriveMode>(DriveMode.drive_joystick)
  const [sensors, setSensors] = createSignal<Array<Sensor | null>>([null, null, null, null])
  const [motors, setMotors] = createSignal<Array<Sensor | null>>()
  const [portsView, setPortsView] = createSignal<boolean>()

  const goToPortsView = () => {
    setPortsView(true)
    setEditedIndex(null);
    setEdited(null);
  }

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

  const handleDriveChange = (event: Event) => {
    const target = event.target as HTMLSelectElement;
    setDriveMode(target.value as DriveMode);
    const newConfig = Object.assign({}, config()) as RobotConfig
    const driveConfigBlocklyItem = newConfig.blocklyList.find((e) => e.builtinScriptName)
    if (!driveConfigBlocklyItem) throw Error('no drive mode in condfig!')
    driveConfigBlocklyItem.builtinScriptName = target.value as DriveMode
    setConfig(newConfig)
  }



  const updateConfigString = (e: Event) => setConfigString((e.target as HTMLTextAreaElement).value || '')


  return (
    <div >
      <div class={styles.controller}>
        <div class={styles.column}>
          <div>
            <h4>Joystick mode</h4>
            <select value={driveMode()} onChange={handleDriveChange}>
              <For each={Object.values(DriveMode)}>{(mode) =>
                <option value={mode}>{mode}</option>
              }</For>
            </select>

            <p>
              <Show when={!configString()}>
                <button onClick={() => { setConfigString(JSON.stringify(config(), null, 2)); setEdited(null) }}>RAW config</button>
              </Show>
              {/* <Show when={configString()}>
                <button disabled={!saveRawEnabled()} onClick={() => saveRawConfig()}>SAVE RAW</button>
              </Show> */}
            </p>

            <p>
              <button onClick={handleSend} disabled={!isSendEnabled()}>Send</button>
            </p>

          </div>

        </div>
        <div class={styles.editor}></div>
        <div>
          <h3>Sensors</h3>
          <table class={styles.configurationTable}>
            <thead>
              <tr>
                <td>Index</td>
                <td>Type</td>
              </tr>
            </thead>
            <tbody>
              {sensors().map((s, i) => (<tr>
                <td>{i}</td>
                <td>{!s ? (<>NULL</>) : (<>X</>)}</td>
              </tr>))}
            </tbody>
          </table>
        </div>
        <div>
        <h3>Motors</h3>
          <table class={styles.configurationTable}>
            <thead>
              <tr>
                <td>Index</td>
                <td>Type</td>
              </tr>
            </thead>
            <tbody>
              {sensors().map((s, i) => (<tr>
                <td>{i}</td>
                <td>{!s ? (<>NULL</>) : (<>X</>)}</td>
              </tr>))}
            </tbody>
          </table>
        </div>

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

export default ConfigurationView;
