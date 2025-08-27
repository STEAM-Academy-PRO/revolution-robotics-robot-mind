
import * as cocoSsd from '@tensorflow-models/coco-ssd';
import '@tensorflow/tfjs';
import { Accessor, createEffect, createSignal, onCleanup } from 'solid-js';



type Props = {
  src: string;
  doDetect: Accessor<boolean>;
  onDetect?: (predictions: cocoSsd.DetectedObject[]) => void;
};



export default function ObjectDetector(props: Props) {
  let imgRef: HTMLImageElement | undefined;
  let canvasRef: HTMLCanvasElement | undefined;

  const [modelLoading, setModelLoading] = createSignal(false);
  let model: cocoSsd.ObjectDetection | null = null;

  const loadModel = async () => {
    setModelLoading(true);
    return await cocoSsd.load().then((loadedModel: cocoSsd.ObjectDetection) => {
      model = loadedModel;
    });
  }

  createEffect(async () => {
    if (props.doDetect() && imgRef && canvasRef) {
      if (!model){
        await loadModel();
      }
      detect();
    }
    if (!props.doDetect()) {
      if (!canvasRef) return;
      const ctx = canvasRef.getContext('2d');
      if (!ctx) return;

      ctx.clearRect(0, 0, canvasRef.width, canvasRef.height);
    }
  })


  const detect = async () => {
    if (!imgRef || !canvasRef || !model) return;

    console.log('detect')

    const predictions = await model.detect(imgRef);

    setModelLoading(false);

    const ctx = canvasRef.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, canvasRef.width, canvasRef.height);
    // ctx.drawImage(imgRef, 0, 0, canvasRef.width, canvasRef.height);

    predictions.forEach((pred: cocoSsd.DetectedObject) => {
      const [x, y, width, height] = pred.bbox;
      ctx.strokeStyle = '#00FFFF';
      ctx.lineWidth = 2;
      ctx.strokeRect(x, y, width, height);
      ctx.font = '16px sans-serif';
      ctx.fillStyle = '#00FFFF';
      ctx.fillText(pred.class, x, y > 10 ? y - 5 : 10);
    });
    if (props.doDetect()) {
      setTimeout(detect, 2000)
    }
  }


  return (
    <div style={{ display: 'flex',
    'justify-content': 'center', 'align-items': 'center', width: '100%', height: '100%' }}>
      <div style={{ position: 'relative', width: '640px', height: '480px' }}>
        <img
          ref={imgRef}
          src={props.src}
          width="640"
          height="480"
          crossorigin="anonymous"
        />
        <canvas ref={canvasRef} width="640" height="480" style={{position: 'absolute', top: 0, left: 0}} />
        {modelLoading() && <div>Loading model…</div>}
      </div>
    </div>
  );
}
