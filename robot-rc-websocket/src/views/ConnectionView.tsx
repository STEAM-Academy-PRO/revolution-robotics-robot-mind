import { Accessor, createEffect } from 'solid-js'
import { SocketWrapper } from '../utils/Communicator';

import styles from './Connection.module.css'
import { Log, clearLog } from '../utils/log';
import { blocklyUrlBase, endpoint, setBlocklyUrlBase, setEndpoint } from '../settings';

export default function ConnectionView({
  connect,
  connection,
  disconnect
}
  : {
    connect: () => void
    disconnect: () => void
    connection: Accessor<SocketWrapper | null>
  }) {


  return (
    <div>
      <div>
        Robot on IP:
        <input type="text" value={endpoint()} onInput={(e) => setEndpoint(e.target.value)} />
        {!connection() ?
        <button onClick={connect}>Connect</button> :
        <button onClick={disconnect}>Disconnect</button>
      }
      </div>
      <div>
        Blockly Endpoint:
        <input type="text" value={blocklyUrlBase()} onInput={(e) => setBlocklyUrlBase(e.target.value)} />
      </div>
      
      <div>
        <Log />
      </div>
    </div>
  );
}

