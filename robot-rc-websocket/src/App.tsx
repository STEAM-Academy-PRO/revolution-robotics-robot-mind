import styles from './App.module.css';

import { createSignal, createMemo, Switch, Match } from 'solid-js'

import ConfigView from './views/ConfigView';
import PlayView from './views/PlayView';
import SettingsView from './views/SettingsView';
import CodeView from './views/CodeView';

import { connLoading, connectOrDisconnect } from './utils/Communicator';
import { conn } from './settings';

// Load default config as fallback.

function App() {

  const [tab, setTab] = createSignal('configure')

  const isActive = createMemo(() => tab() === 'play')

  const menuItems = [{
    id: 'configure',
    label: 'Configure',
    children: <ConfigView />
  },
  {
    id: 'code',
    label: 'Code',
    children: <CodeView />
  },
  {
    id: 'play',
    label: 'Play',
    children: <PlayView isActive={isActive} />
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
        <div onClick={() => connectOrDisconnect()} class={styles.clickable}>
          {conn() ? <>🟢</> : connLoading() ? <>🟡</> : <>🔴</>}
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
