import { createEffect, createSignal, onCleanup, onMount } from "solid-js";
import styles from "./AiRcView.module.css";
import { BlocklyView } from "./BlocklyView";
import { fetchAiXmlResponse, fixXmlError } from "../utils/ai";
import { RRController } from "../utils/program-runner";
import { conn } from "../settings";
import { currentConfig } from "../utils/Config";
import aiBlocklyPrompt from "./utils/ai-blockly-prompt";

const queryErrorCache: { [key: string]: number } =
JSON.parse(
  localStorage.getItem("ai-rc-query-error-cache") || "{}"
);


function AiRcView() {
  // @ts-ignore
  const SpeechRecognition = window.webkitSpeechRecognition;

  const recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.continuous = true; // or true for continuous listening
  recognition.interimResults = true;

  let promptEditorRef!: HTMLTextAreaElement;

  let lastXml = localStorage.getItem("ai-rc-code") || "";

  const [xml, setXml] = createSignal<string>(lastXml);
  const [isListening, setIsListening] = createSignal(false);
  const [text, setText] = createSignal<string>(
    "go forward 30cm then turn right and repeat this 4 times"
  );
  const [isPromptEditorOpen, setIsPromptEditorOpen] =
    createSignal<boolean>(false);
  const [isLoadingPrompt, setIsLoadingPrompt] = createSignal<boolean>(false);

  const onSave = (code: string) => {
    // console.log('AI RC code saved:', code, arguments);
    localStorage.setItem("ai-rc-code", code);
    // setXml(code);
  };

  recognition.onresult = (event: any) => {
    let fullTranscript = "";
    for (let i = 0; i < event.results.length; i++) {
      fullTranscript += event.results[i][0].transcript + "n";
    }
    setText(fullTranscript);
  };

  createEffect(async () => {
    if (isListening()) {
      console.log("AI RC listening started");
      recognition.start();
    } else {
      console.log('AI RC listening stopped');
      recognition.stop();
    }
  }, [isListening]);

  const sendQuery = async () => {
    if (isLoadingPrompt()) {
      return;
    }
    setIsLoadingPrompt(true);
    setXml("");
    const responseJson = await fetchAiXmlResponse(text());

    console.log("AI RC response:", responseJson);
    setXml(responseJson.xml);
    setIsLoadingPrompt(false);
  };


  const uploadAndStart = async (pythonCode: string) => {
    const connection = conn()
    if (!connection) {
      console.error("No connection to the robot. Please connect first.");
      return;
    }
    await new RRController(connection, currentConfig()).start(pythonCode);
  }

  const onLoadError = async (message: string, xml: string) => {
    console.error("Error loading AI RC code:", message);

    queryErrorCache[text()] = (queryErrorCache[text()] || 0) + 1;
    localStorage.setItem("ai-rc-query-error-cache", JSON.stringify(queryErrorCache));

    if (queryErrorCache[text()] > 3) {
      console.warn("Too many errors for this query, AI Failed!");
    }

    const fixedXml = await fixXmlError(aiBlocklyPrompt + '\n' + text(), xml, message)
    setXml(fixedXml);
    console.log("AI RC code fixed:", fixedXml);
    uploadAndStart(fixedXml);
  };

  const onCodeReload = (code: string) => {
    console.log("AI RC code reloaded:", code);
    // Should only reload once
    uploadAndStart(code);
  };



  return (
    <div>
      <button
        class={styles.ai}
        classList={{ [styles.listening]: isListening() }}
        disabled={isLoadingPrompt()}
        onClick={() => {
          setIsListening(!isListening());
          setIsPromptEditorOpen(false);
          if (!isListening()) {
            sendQuery();
          }
        }}
      >
        Tell me what should I do?
      </button>

      <button
        class={styles.textButton}
        onClick={() => {
          setIsPromptEditorOpen(!isPromptEditorOpen());
          if (!isPromptEditorOpen()) {
            sendQuery();
          }
        }}
      >
        <span class={styles.icon} role="img" aria-label="keyboard">
          ⌨️
        </span>
      </button>

      <div></div>
      {text() && (
        <div
          class={styles.prompt}
          innerHTML={text().replace(/n/g, "<br />")}
        ></div>
      )}
      {isPromptEditorOpen() && (
        <div class={styles.promptEditor}>
          <textarea
            ref={promptEditorRef}
            value={text()}
            onInput={(e) => {
              setText(e.currentTarget.value);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                setIsPromptEditorOpen(false);
                sendQuery();
              }
            }}
          ></textarea>
        </div>
      )}

      <BlocklyView
        onSave={onSave}
        xml={xml}
        reloadCode={onCodeReload}
        onLoadError={onLoadError}
      ></BlocklyView>
    </div>
  );
}

export default AiRcView;
