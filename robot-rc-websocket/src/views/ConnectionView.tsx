import { createSignal, Accessor, Setter, createEffect, onCleanup } from 'solid-js'
import { SocketWrapper, WSEventType, connectToRobot } from '../utils/Communicator';

import styles from './Connection.module.css'

export default function ConnectionView({
  endpoint,
  setEndpoint,
  connect,
  connection,
  disconnect,
  log,
  setLog
}
  : {
    connect: () => void
    disconnect: () => void
    setEndpoint: Setter<string>,
    endpoint: Accessor<string>,
    connection: Accessor<SocketWrapper | null>
    log: Accessor<string>
    setLog: Setter<string>
  }) {

  createEffect(() => {
    localStorage.setItem('endpoint', endpoint());
  });

  return (
    <div>

      Robot on IP:n
      <input type="text" value={endpoint()} onInput={(e) => setEndpoint(e.target.value)} />

      {!connection() ?
        <button onClick={connect}>Connect</button> :
        <button onClick={disconnect}>Disconnect</button>
      }
      <div>
        <button onClick={() => setLog('')}>clear</button> :
        <pre class={styles.log}>
          {log()}
        </pre>
      </div>
    </div>
  );
}

