import { createSignal, createEffect, Accessor, Setter } from 'solid-js'

import styles from './SimpleConfigSender.css'

import { RobotMessage, SocketWrapper } from '../utils/Communicator';

function ConfigurationView({
  config, setConfig,
  conn
}: {config: Accessor<any>, setConfig: Setter<any>, conn: Accessor<SocketWrapper|null>}) {

  const [response, setResponse] = createSignal('');
  const [isSendEnabled, setIsSendEnabled] = createSignal(false);

  createEffect(() => {
    try{
        JSON.parse(config())
        setIsSendEnabled(Boolean(conn()))
    } catch(e){
        setIsSendEnabled(false)
    }
  });

  const handleSend = ()=>{
    conn()?.send(RobotMessage.configure, JSON.stringify(config()))
  }

  // const handleSendHTTP = async () => {
    
  //   const parsedConfig = JSON.parse(config())
  //   try {

  //   // apparently, with no-cors you can not simply post a JSON...
  //   // @see https://stackoverflow.com/questions/39689386/fetch-post-json-data-application-json-change-to-text-plain

  //     const requestOptions = {
  //       method: 'POST',
  //       headers: {
  //           'Accept': 'application/json',
  //           'Content-Type': 'application/json'
  //         },
  //       body: JSON.stringify(parsedConfig)
  //     };

  //     const result = await fetch('http://' + endpoint() + ':8080/configure', requestOptions);
  //     const data = await result.json();

  //     setResponse(data);
  //   } catch (error) {
  //     console.error('Error sending request:', error);
  //   }
  // };

  return (
    <div>
      <h1>Upload Configuration</h1>
      <br />
      <textarea class={styles.textarea} value={config()} onInput={(e) => setConfig(e.target.value)} />
      <button onClick={handleSend} disabled={!isSendEnabled()}>Send</button>
      {response() && (
        <div>
          <h2>Response</h2>
          <pre>{JSON.stringify(response(), null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default ConfigurationView;
