import { createSignal, Accessor, Setter, createEffect, onCleanup } from 'solid-js'
import { SocketWrapper, WSEventType, connectToRobot } from '../utils/Communicator';

import styles from './ConnectionView.css'

export default function ConnectionView({
  setConn, conn }: {
    setConn: Setter<SocketWrapper | null>, conn: Accessor<SocketWrapper | null>
  }) {

  const [endpoint, setEndpoint] = createSignal(localStorage.getItem('endpoint') || '');
  const [_log, setLog] = createSignal<string>('')

  const log = (msg: any) => {
    if (!msg) return
    setLog(_log() + `\n[${new Date().toLocaleTimeString('en-US', { hour12: false })}] ${msg}`)
  }

  const connect = () => {
    const socket = connectToRobot(endpoint())
    socket.on(WSEventType.onMessage, (e)=>{log(e)})
    socket.on(WSEventType.onOpen, (e)=>{log('Socket Connection Established!')})
    socket.on(WSEventType.onClose, (wasClean)=>{
      log(wasClean?'Socket Connection Closed Nicely!':'Socket Connection Dropped.')
      setConn(null)
    })
    socket.on(WSEventType.onError, (e)=>{log(e)})
    setConn(socket)
  }
  const disconnect = () => {
    if (conn()) {
      conn()?.close()
      setConn(null);
    }
  }

  createEffect(() => {
    localStorage.setItem('endpoint', endpoint());
  });

  return (
    <div>

      Robot on IP:n
      <input type="text" value={endpoint()} onInput={(e) => setEndpoint(e.target.value)} />

      {!conn() ?
        <button onClick={connect}>Connect</button> :
        <button onClick={disconnect}>Disconnect</button>
      }
      <pre class={styles.log}>
        {_log()}
      </pre>
    </div>
  );
}

