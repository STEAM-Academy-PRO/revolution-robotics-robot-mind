// import logo from './logo.svg';
import styles from './App.module.css';

import { createSignal, createEffect, createMemo, Switch, Match } from 'solid-js'
import ConfigurationView from './views/ConfigurationView';
import ControllerView from './views/ControllerView';
import ConnectionView from './views/ConnectionView';
import { SocketWrapper, connectToRobot, disconnect } from './utils/Communicator';

import DEFAULT_JSON from "./assets/robot-config.json"
import { uploadConfig } from './utils/commands';
import { RobotConfig } from './utils/Config';
import CodeView from './views/CodeView';

// Load default config as fallback.
let defaultConfig: RobotConfig = DEFAULT_JSON as RobotConfig
try { defaultConfig = JSON.parse(localStorage.getItem('config') || '') as RobotConfig || DEFAULT_JSON} catch (e){}

function App() {
  const [conn, setConn] = createSignal<SocketWrapper|null>(null)
  const [connLoading, setConnLoading] = createSignal<boolean>(false)
  const [config, setConfig] = createSignal<RobotConfig>(defaultConfig);
  const [tab, setTab] = createSignal('configure')
  const [endpoint, setEndpoint] = createSignal(localStorage.getItem('endpoint') || '');
  const [_log, setLog] = createSignal<string>('')

  const isActive = createMemo(()=>tab() === 'play')

  // When switching to play mode, automatically upload the config!
  createEffect(()=>{if (tab() === 'play') {uploadConfig(conn(), config())};})

  const log = (msg: any) => {
    if (!msg) return
    setLog(_log() + `\n[${new Date().toLocaleTimeString('en-US', { hour12: false })}] ${msg}`)
  }

  const connectOrDisconnect = ()=>{
    if (conn()){
      disconnect(conn, setConn)
    } else {
      connectToRobot(setConn, setConnLoading, endpoint, config, log)
    }
  }

  createEffect(() => {
    config()
    localStorage.setItem('config', JSON.stringify(config()));
  });

  const menuItems = [{
      id: 'configure',
      label: 'Configure',
      children: <ConfigurationView config={config} setConfig={setConfig} conn={conn} />
    },
    {
      id: 'code',
      label: 'Code',
      children: <CodeView config={config} setConfig={setConfig} conn={conn} />
    },
    {
      id: 'play',
      label: 'Play',
      children: <ControllerView conn={conn} isActive={isActive} log={_log} setLog={setLog} endpoint={endpoint}/>
    },
    {
      id: 'connect',
      label: 'Connection',
      children: <ConnectionView
        endpoint={endpoint} setEndpoint={setEndpoint}
        connect={()=>connectToRobot(setConn, setConnLoading, endpoint, config, log)}
        disconnect={()=>disconnect(conn, setConn)}
        connection={conn}
        log={_log} setLog={setLog}
      />
    }
  ]

  return (
    <div class={styles.App}>
      <div class={styles.header}>
        <ul class={styles.headerUl}>
          {menuItems.map((item) =>
            <li class={styles.headerItem}
              classList={{ [styles.selected]: tab() === item.id }} onClick={() => setTab(item.id)}>
              {item.label}
            </li>
          )}
        </ul>
        <div onClick={()=>connectOrDisconnect()} class={styles.clickable}>
          {conn()?<>🟢</>:connLoading()?<>🟡</>:<>🔴</>}
        </div>

      </div>
      <div class={styles.tabContent}>
        <Switch>
          {menuItems.map((item) =>
            <Match when={tab() === item.id}>
              {item.children}
            </Match>
          )}
        </Switch>
      </div>
    </div>
  );
}



export default App;
