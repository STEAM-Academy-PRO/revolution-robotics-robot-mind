import { createEffect, createSignal } from "solid-js";

const [endpoint, setEndpoint] = createSignal(localStorage.getItem('endpoint') || 'raspberrypi.local');
const [blocklyUrlBase, setBlocklyUrlBase] = createSignal(localStorage.getItem('blockly') || 'https://test.rr.scapps.io');

createEffect(() => {
    localStorage.setItem('endpoint', endpoint());
});

createEffect(() => {
    localStorage.setItem('blockly', blocklyUrlBase());
});


export { endpoint, setEndpoint, blocklyUrlBase, setBlocklyUrlBase }