import { createSignal, createEffect, createMemo, onCleanup } from 'solid-js'
import { RobotMessage, SocketWrapper } from '../utils/Communicator';

export default function ControllerView({ conn, on }: { conn: SocketWrapper | null, on: boolean }) {

  const [x, setX] = createSignal(0);
  const [y, setY] = createSignal(0);

  let i = 0

  const interval = setInterval(() => {
    // if (!on){ return }
    // const controlMessage
    const ctrlArray = new Uint8Array([
      i++ % 127, // keepalive - no need to change this as it's bluetooth specific
      mapAnalogNormal(x()), // UInt8, left-right analog, value range: 0-255
      mapAnalogNormal(y()), // UInt8, bottom-top analog, value range: 0-255

      0, // unused analog);
      0, // unused analog
      0, // unused analog
      0, // unused analog

      0, // UInt8, button group 1, 1 button per bit
      0, // UInt8, button group 2, 1 button per bit
      0, // UInt8, button group 3, 1 button per bit
      0, // UInt8, button group 4, 1 button per bit

      0, // Reserved
      0, // Reserved
      0, // Reserved
      0, // Reserved
      0  // Reserved                    parsed_config = RobotConfig.from_string(json.loads(message["body"]))

    ])

    conn()?.send(RobotMessage.control, ctrlArray)
  }, 100)

  onCleanup(() => {
    clearInterval(interval)
  })

   // Function to update joystick position based on mouse event
  const updatePosition = (event) => {
    try{
      const rect = event.currentTarget.getBoundingClientRect();
      const offsetX = event.clientX - rect.left;
      const offsetY = event.clientY - rect.top;

      // Normalize the position to be between -1 and 1
      const normalizedX = (offsetX / rect.width) * 2 - 1;
      const normalizedY = (offsetY / rect.height) * 2 - 1;

      // Update signals
      setX(normalizedX);
      setY(normalizedY); // Invert Y to match typical coordinate systems
      console.warn(normalizedX, normalizedY)
    } catch(e){

    }
  };

  const reset = () => {setX(0); setY(0)}
  onCleanup(() => {
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
  });

  let isDragging = false;

  // Function to handle mouse down event
  const handleMouseDown = (event) => {
    isDragging = true;
    updatePosition(event);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  // Function to handle mouse move event
  const handleMouseMove = (event) => {
    if (isDragging) {
      updatePosition(event);
    }
  };

  // Function to handle mouse up event
  const handleMouseUp = () => {
    isDragging = false;
    setX(0); setY(0);
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
  };

  return (
      <div>
        <h1>Controller</h1>
        <div
        style={{
          position: 'relative',
          width: '200px',
          height: '200px',
          borderRadius: '50%',
          background: '#eee',
          cursor: 'grab',
        }}
        onmousedown={handleMouseDown}
      >
        {/* Display the joystick handle */}
        <div
          style={{
            position: 'absolute',
            width: '40px',
            height: '40px',
            borderRadius: '50%',
            background: '#3498db',
            top: `${50 + y() * 50}%`, // Adjust position based on y signal
            left: `${50 + x() * 50}%`, // Adjust position based on x signal
            transform: 'translate(-50%, -50%)',
            cursor: 'grabbing',
            pointerEvents: 'none', // Allow mouse events to pass through
          }}
        ></div>
      </div>
    </div>
  );
}

function mapAnalogNormal(val: number) {
  return mapValue(val, -1, 1, 0, 255)
}

function mapValue(value: number, inMin: number, inMax: number, outMin: number, outMax: number) {
  // Map the value from the input range to the output range
  const mappedValue = (value - inMin) * (outMax - outMin) / (inMax - inMin) + outMin;

  // Round the mapped value
  return Math.floor(mappedValue);
}