import styles from './App.module.css';

import { createSignal, createMemo, Switch, Match } from 'solid-js'

import ConfigView from './views/ConfigView';
import PlayView from './views/PlayView';
import SettingsView from './views/SettingsView';
import CodeView from './views/CodeView';

import { connLoading, connectOrDisconnect, connectToRobot } from './utils/Communicator';
import { conn, setEndpoint } from './settings';
import BlocklyAIView from './views/BlocklyAiView';

// Load default config as fallback.

function App() {

  const [tab, setTab] = createSignal('configure')

  const isActive = createMemo(() => tab() === 'play')

  const menuItems = [{
    id: 'configure',
    label: 'Configure ⚙️',
    children: <ConfigView />
  },
  {
    id: 'code',
    label: 'Code 💻',
    children: <CodeView />
  },
  {
    id: 'blocklyAi',
    label: 'Blockly AI 🤖',
    children: <BlocklyAIView />
  },
  {
    id: 'play',
    label: 'Play 🕹️',
    children: <PlayView isActive={isActive} />
  },
  {
    id: 'connection_settings',
    label: '🔗',
    children: <SettingsView />
  },
  ]

  const isEmbedded = location.hostname.endsWith(".local") || location.search.includes("address=");
  if (isEmbedded) {
    const robotEndpoint = location.hostname.endsWith(".local")?location.hostname : new URLSearchParams(location.search).get("address");
    if (robotEndpoint){
      setEndpoint(robotEndpoint);
      connectToRobot();
    }
  }


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
