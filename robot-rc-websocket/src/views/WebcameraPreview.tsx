import { createSignal, onCleanup, createEffect, Show } from "solid-js";
import { log } from "../utils/log";

export const WebcameraPreview = () => {

  let preview: HTMLVideoElement
  let stream: MediaStream

  // Function to get the media stream from the camera
  const getVideoStream = async () => {
    try {
      stream = await navigator.mediaDevices.getUserMedia({ video: true });
      // setVideoStream(stream);
      console.log('stream', stream)
      setState('on')
      preview.srcObject = stream
    } catch (error) {
      console.error("Error accessing camera:", error);
      log('x -' + navigator.mediaDevices)
      log("Error accessing camera, " + error)
      
    }
  };

  // Clean up function to stop the media stream when component unmounts
  onCleanup(() => {
    
  });
  
  const off = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }
    setState('off')
  }

  const [state, setState] = createSignal('off');

  // Render the video element for preview
  return (
    <div>
      <Show when={state() === 'off'}>
        <button onClick={getVideoStream}>On</button>
      </Show>
      <Show when={state() === 'on'}>
      <button onClick={()=>off()}>Off</button>
      {(
        <video ref={preview!} autoPlay={true} playsInline={true} width="300" height="200" />
      )}
      </Show>
    </div>
  );
};
