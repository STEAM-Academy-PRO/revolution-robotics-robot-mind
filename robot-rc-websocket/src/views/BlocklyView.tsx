import { Accessor, createEffect, createSignal, on, onMount } from "solid-js";
import { blocklyUrlBase } from "../settings";
import styles from "./Blockly.module.css";
import { formatXml } from "../utils/xml-formatter";

export function BlocklyView({
  onSave,
  onLoadError,
  xml,
  reloadCode,
}: {
  onSave: (xml: string, python: string) => void;
  onLoadError?: (message: string, xml: string) => void;
  xml: string | Accessor<string>;
  reloadCode?: (code: string) => void;
}) {
  let blocklyRef!: HTMLIFrameElement;
  let xmlString = typeof xml === "function" ? xml() : xml;
  let oncePerLoad = false;

  // const [error, setError] = createSignal<string | undefined>();

  onMount(() => {
    // console.log('BlocklyView mounted', blocklyRef);
    let debounceTimeout: number | undefined;
    window.addEventListener("message", (event) => {
      switch (event.data.type) {
        case "save":
          if (oncePerLoad) {
            oncePerLoad = false; // Reset after first load
            reloadCode?.(event.data.python);
          }
          break;
        case "load_error":
          // setError(event.data.message + "\n" + formatXml(event.data.xml));
          onLoadError?.(event.data.message, formatXml(event.data.xml))
          break;
        }

        if (debounceTimeout) clearTimeout(debounceTimeout);
        debounceTimeout = window.setTimeout(() => {
            if (event.data.type !== "save") return;
            onSave(event.data.xml, event.data.python);
        }, 300); // 300ms debounce
    });
    blocklyRef.onload = () => {
      if (blocklyRef.contentWindow) {
        const x = xmlString;
        blocklyRef.contentWindow.postMessage({ type: "init", xml: x }, "*");
      } else {
        console.error("Blockly iframe contentWindow is not available");
      }
    };
  });

  createEffect(() => {
    let xmlString = typeof xml === "function" ? xml() : xml;
    // console.log('BlocklyView xml changed:', xmlString);
    if (xmlString && blocklyRef?.contentWindow) {
      oncePerLoad = true; // Prevents multiple loads
      blocklyRef.contentWindow.postMessage(
        { type: "load", xml: xmlString },
        "*"
      );
    }
  });

  return (
    <div>
      <iframe
        ref={blocklyRef}
        class={styles.blockly}
        sandbox="allow-scripts allow-same-origin"
        src={`${blocklyUrlBase()}/interface.html`}
      ></iframe>
    </div>
  );
}
