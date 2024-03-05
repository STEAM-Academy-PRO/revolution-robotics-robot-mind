import { createEffect, createSignal } from "solid-js";
import { SocketWrapper } from "./utils/Communicator";

export const [conn, setConn] = createSignal<SocketWrapper | null>(null)
export const [endpoint, setEndpoint] = createSignal(localStorage.getItem('endpoint') || 'raspberrypi.local');
export const [blocklyUrlBase, setBlocklyUrlBase] = createSignal(localStorage.getItem('blockly') || 'https://test.rr.scapps.io');

createEffect(() => {
    localStorage.setItem('endpoint', endpoint());
});

createEffect(() => {
    localStorage.setItem('blockly', blocklyUrlBase());
});

