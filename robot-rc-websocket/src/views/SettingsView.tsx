import { connectToRobot, disconnect } from '../utils/Communicator';
import { blocklyUrlBase, conn, endpoint, setBlocklyUrlBase, setEndpoint } from '../settings';
import styles from './Config.module.css'

export default function SettingsView() {

  return (
    <div>
      <h3>Connection</h3>
      <div>
        Robot on IP:<br />
        <input type="text" value={endpoint()} onInput={(e) => setEndpoint(e.target.value)} />
        <br />
        {!conn() ?
          <button class={`${styles.btn} ${styles.connect}`} onClick={connectToRobot}>Connect</button> :
          <button class={styles.btn} onClick={disconnect}>Disconnect</button>
        }
      </div>
      <div>
        <br />
        Blockly Endpoint:<br />
        <input type="text" value={blocklyUrlBase()} onInput={(e) => setBlocklyUrlBase(e.target.value)} />
      </div>

    </div >
  );
}

