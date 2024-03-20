import { createSignal } from "solid-js";

interface Device {
  id: string;
  name: string;
  gatt: {
    connect: () => Promise<any>;
    connected: boolean;
  };
}


export function BLESelector() {
  const [devices, setDevices] = createSignal<Device[]>([]);

  const requestDevice = async () => {
    try {
      const device = await navigator.bluetooth.requestDevice({
        acceptAllDevices: true
      }) as Device;
      setDevices([...devices(), device]);
    } catch (error) {
      console.error("Bluetooth device request failed:", error);
    }
  };

  const connectDevice = async (device: Device) => {
    if (device.gatt.connected) {
      return;
    }
    try {
      const server = await device.gatt.connect();
      console.log("Connected to", server.device.name);
    } catch (error) {
      console.error("Bluetooth device connection failed:", error);
    }
  };

  return (
    <>
      <button onClick={requestDevice}>Find Devices</button>
      <ul>
        {devices().map(device => (
          <li key={device.id} onClick={() => connectDevice(device)}>
            {device.name}
          </li>
        ))}
      </ul>
    </>
  );
}