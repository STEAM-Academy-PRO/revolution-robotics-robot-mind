// import logo from './logo.svg';
import styles from './App.module.css';

import { createSignal, createEffect, createMemo, Switch, Match } from 'solid-js'
import ConfigurationView from './views/ConfigurationView';
import ControllerView from './views/ControllerView';
import ConnectionView from './views/ConnectionView';
import { SocketWrapper, connectToRobot, disconnect } from './utils/Communicator';

import json from "./assets/robot-config.json"

function App() {
  const [conn, setConn] = createSignal<SocketWrapper|null>(null)
  const [connLoading, setConnLoading] = createSignal<boolean>(false)
  const [config, setConfig] = createSignal(localStorage.getItem('config') || JSON.stringify(json, null, 2));
  const [tab, setTab] = createSignal('configure')
  const [endpoint, setEndpoint] = createSignal(localStorage.getItem('endpoint') || '');
  const [_log, setLog] = createSignal<string>('')

  const isActive = createMemo(()=>tab() === 'play')

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
    try{
        JSON.parse(config())
        localStorage.setItem('config', config());
    } catch(e){}
  });

  const menuItems = [{
      id: 'configure',
      label: 'Configure',
      children: <ConfigurationView config={config} setConfig={setConfig} conn={conn} />
    },
    {
      id: 'play',
      label: 'Play',
      children: <ControllerView conn={conn} isActive={isActive}/>
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
        <div onClick={()=>connectOrDisconnect()}>
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
