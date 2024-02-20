import { createSignal, Accessor, Setter, createEffect, onCleanup } from 'solid-js'
import { SocketWrapper, WSEventType, connectToRobot } from '../utils/Communicator';

import styles from './Connection.module.css'
import { clearLog, getLog } from '../utils/log';

export default function ConnectionView({
  endpoint,
  setEndpoint,
  connect,
  connection,
  disconnect
}
  : {
    connect: () => void
    disconnect: () => void
    setEndpoint: Setter<string>,
    endpoint: Accessor<string>,
    connection: Accessor<SocketWrapper | null>
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
        <button onClick={() => clearLog()}>clear</button> :
        <pre class={styles.log}>
          {getLog()}
        </pre>
      </div>
    </div>
  );
}

