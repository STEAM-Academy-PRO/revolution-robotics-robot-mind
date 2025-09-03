import { createEffect, createSignal } from "solid-js";
import { SocketWrapper } from "./utils/Communicator";

export const [conn, setConn] = createSignal<SocketWrapper | null>(null)
export const [endpoint, setEndpoint] = createSignal(localStorage.getItem('endpoint') || location.hostname || 'raspberrypi.local');

// TODO: My locally hosted blockly: http://localhost/robot/blockly/ - make it a package.
export const [blocklyUrlBase, setBlocklyUrlBase] = createSignal(localStorage.getItem('blockly') || 'blockly');

createEffect(() => {
    localStorage.setItem('endpoint', endpoint());
});

createEffect(() => {
    localStorage.setItem('blockly', blocklyUrlBase());
});

