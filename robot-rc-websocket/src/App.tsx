// import logo from './logo.svg';
import styles from './App.module.css';

import { createSignal, createEffect, createMemo, Switch, Match } from 'solid-js'
import ConfigurationView from './views/ConfigurationView';
import ControllerView from './views/ControllerView';
import ConnectionView from './views/ConnectionView';
import { SocketWrapper } from './utils/Communicator';

import json from "./assets/robot-config.json"

function App() {
  const [conn, setConn] = createSignal<SocketWrapper|null>(null)
  const [config, setConfig] = createSignal(localStorage.getItem('config') || JSON.stringify(json, null, 2));
  const [tab, setTab] = createSignal('configure')

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
      children: <ControllerView conn={conn} on={tab() === 'play'}/>
    },
    {
      id: 'connect',
      label: 'Connection',
      children: <ConnectionView setConn={setConn} conn={conn}/>
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
        <div>
          {conn()?<>🟢</>:<>🔴</>}
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
