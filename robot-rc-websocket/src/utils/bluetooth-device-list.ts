import { createSignal } from "solid-js";

export const [bluetoothDeviceIds, setBluetoothDeviceIds] = createSignal<string[]>([]);

export async function searchBluetoothDevices() {
try {
    // @ts-ignore
    const device = await navigator.bluetooth.requestDevice({
        filters: [{services: ['d2d5558c-5b9d-11e9-8647-d663bd873d93']}]
        // acceptAllDevices: true,
    });
    console.log('Selected device:', device.name);
    return device.name;
  } catch (error) {
    console.error('Bluetooth error:', error);
  }
}
