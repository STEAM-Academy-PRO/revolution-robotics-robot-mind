
import * as cocoSsd from '@tensorflow-models/coco-ssd';
import '@tensorflow/tfjs';
import { Accessor, createEffect, createSignal, onCleanup, Show } from 'solid-js';



type Props = {
  src: string;
  doDetect: Accessor<boolean>;
  onDetect?: (predictions: cocoSsd.DetectedObject[]) => void;
};



export default function ObjectDetector(props: Props) {
  let imgRef: HTMLImageElement | undefined;
  let canvasRef: HTMLCanvasElement | undefined;
  let containerRef: HTMLDivElement | undefined;

  const [modelLoading, setModelLoading] = createSignal(false);
  let model: cocoSsd.ObjectDetection | null = null;

  const [width, setWidth] = createSignal(640);
  const [height, setHeight] = createSignal(480);
  const [top, setTop] = createSignal(0);
  const [left, setLeft] = createSignal(0);

  const measure = () => {
    if (!imgRef || !containerRef) return;
    const rect = imgRef.getBoundingClientRect();
    const containerRect = containerRef.getBoundingClientRect();
    setWidth(Math.round(rect.width));
    setHeight(Math.round(rect.height));
    setTop(Math.round(rect.top - containerRect.top));
    setLeft(Math.round(rect.left - containerRect.left));
    // Ensure canvas drawing buffer matches CSS size
    if (canvasRef) {
      canvasRef.width = Math.round(rect.width);
      canvasRef.height = Math.round(rect.height);
    }
  };

  createEffect(() => {
    // Measure when refs exist
    if (imgRef && containerRef) measure();
  });

  // Recalculate on window resize
  const onResize = () => measure();
  window.addEventListener('resize', onResize);
  onCleanup(() => window.removeEventListener('resize', onResize));

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
      <div ref={containerRef} style={{ position: 'relative', 'height': '100%', 'width': '100%'}}>
        <div style={{position: 'absolute', top: 0, left: 0, width: '100%', 'max-height': '100vh', 'background-color': 'rgba(255, 0, 0, 0.1)'}}></div>
        <img
          ref={imgRef}
          src={props.src}
          crossorigin="anonymous"
          style={{ height: 'calc(100vh - 60px)', width: 'auto', 'object-fit': 'contain', 'margin-top': '60px' }}
          onLoad={measure}
        />
        <Show when={props.doDetect()}>
          <canvas
            ref={canvasRef}
            style={{ position: 'absolute', top: `${top()}px`, left: `${left()}px`, width: `${width()}px`, height: `${height()}px`, 'pointer-events': 'none' }}
          />
        </Show>
        {modelLoading() && <div>Loading model…</div>}
      </div>
    </div>
  );
}
