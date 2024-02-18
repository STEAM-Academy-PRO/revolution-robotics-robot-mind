import { createMemo, createSignal } from "solid-js";

const [_log, setLog] = createSignal<string>("");

export const log = (msg: any) => {
  if (!msg) return;
  setLog(
    _log() +
      `\n[${new Date().toLocaleTimeString("en-US", { hour12: false })}] ${msg}`
  );
};

export const getLog = createMemo(()=>_log())

export const clearLog = () => {
    setLog('')
}