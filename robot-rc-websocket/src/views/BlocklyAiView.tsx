import { createEffect, createSignal, onCleanup, onMount, Show } from "solid-js";
import styles from "./AiRcView.module.css";
import { BlocklyView } from "./BlocklyView";
import { fetchAiXmlResponse, fixXmlError } from "../utils/ai";
import { RRController } from "../utils/program-runner";
import { conn } from "../settings";
import { currentConfig } from "../utils/Config";
import aiBlocklyPrompt from "../utils/ai-blockly-prompt";

const queryErrorCache: { [key: string]: number } = JSON.parse(
  localStorage.getItem("ai-rc-query-error-cache") || "{}"
);

function BlocklyAIView() {
  // @ts-ignore
  const SpeechRecognition = window.webkitSpeechRecognition;

  const recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.continuous = true; // or true for continuous listening
  recognition.interimResults = true;

  let promptEditorRef!: HTMLTextAreaElement;
  let rrController: RRController | null = null;

  let lastXml = localStorage.getItem("ai-rc-xml") || "";

  const [xml, setXml] = createSignal<string>(lastXml);
  const [isListening, setIsListening] = createSignal(false);

  const pastConversation = JSON.parse(
    localStorage.getItem("ai-rc-conversation") || "[]"
  );

  const [conversation, setConversation] =
    createSignal<{ message: string; type: string }[]>(pastConversation);
  const [text, setText] = createSignal<string>("");
  const [isPromptEditorOpen, setIsPromptEditorOpen] =
    createSignal<boolean>(false);

  const [isRunning, setIsRunning] = createSignal<boolean>(false);
  const [isLoadingPrompt, setIsLoadingPrompt] = createSignal<boolean>(false);
  const [pythonCode, setPythonCode] = createSignal<string>("");
  const [error, setError] = createSignal<string | undefined>(undefined);

  const onSave = (xml: string, code: string) => {
    localStorage.setItem("ai-rc-xml", code);
    setPythonCode(code);
  };

  recognition.onresult = (event: any) => {
    console.log("AI RC recognition result:", event);
    let fullTranscript = "";
    for (let i = 0; i < event.results.length; i++) {
      fullTranscript += event.results[i][0].transcript + "\n";
    }
    setText(fullTranscript);
  };

  createEffect(async () => {
    if (isListening()) {
      recognition.start();
    } else {
      recognition.stop();
    }
  }, [isListening]);

  const sendQuery = async (forceDisableCache?: boolean) => {
    if (isLoadingPrompt()) {
      return;
    }
    setIsLoadingPrompt(true);
    setXml("");
    const query = conversation()
      .filter((c) => c.type === "ME")
      .map((c) => c.message)
      .join("\n");
    const responseJson = await fetchAiXmlResponse(query, forceDisableCache);

    console.log("AI RC response:", responseJson);
    if (responseJson.error) {
      setConversation([
        ...conversation(),
        { message: responseJson.error, type: "AI_ERROR" },
      ]);
    }
    if (responseJson.xml) {
      setXml(responseJson.xml);
    }

    setIsLoadingPrompt(false);
  };

  const onInputChanged = () => {
    if (text().trim()) {
      setConversation([...conversation(), { message: text().trim(), type: "ME" }]);
      localStorage.setItem(
        "ai-rc-conversation",
        JSON.stringify(conversation())
      );
    }
    setText("");
    sendQuery();
  };

  const onClearConversation = () => {
    setConversation([]);
    localStorage.removeItem("ai-rc-conversation");
    setText("");
  };

  const onStop = () => {
    if (rrController) {
      setIsRunning(false);
      rrController.stop();
      rrController = null;
    }
  };

  const uploadAndStart = async (pythonCode: string) => {
    const connection = conn();
    if (!connection) {
      console.error("No connection to the robot. Please connect first.");
      return;
    }
    setPythonCode(pythonCode);
    rrController = new RRController(connection, currentConfig());
    setIsRunning(true);
    await rrController.start(pythonCode, onStop);
  };

  const onLoadError = async (message: string, xml: string) => {
    if (isLoadingPrompt()) {
      return;
    }
    console.error("Error loading AI RC code. Trying to fix it.",);
    setIsLoadingPrompt(true);
    queryErrorCache[getConversationHash()] = (queryErrorCache[getConversationHash()] || 0) + 1;
    localStorage.setItem(
      "ai-rc-query-error-cache",
      JSON.stringify(queryErrorCache)
    );

    if (queryErrorCache[getConversationHash()] > 3) {
      console.warn("Too many errors for this query, AI Failed!");
      setError(
        `AI failed to fix the code after ${queryErrorCache[getConversationHash()]} attempts.\n\n${xml}`)
      setIsLoadingPrompt(false);
      return;
    }

    const fixedXml = await fixXmlError(
      aiBlocklyPrompt + "\n" + getConversationHash(),
      xml,
      message
    );
    setXml(fixedXml);
    console.log("AI RC code fixed: rev", queryErrorCache[getConversationHash()]);
    setIsLoadingPrompt(false);
  };

  const onCodeReload = (code: string) => {
    console.warn("AI RC code reloaded:", code);
    // Should only reload once
    setPythonCode(code);
    // uploadAndStart(code);
  };

  const getConversationHash = () => {
    return conversation()
      .map((c) => `${c.type}:${c.message}`)
      .join("|"); // lol demo
  };

  return (
    <div>
      <button
        class={styles.aiButton}
        classList={{ [styles.listening]: isListening() }}
        disabled={isLoadingPrompt()}
        onClick={() => {
          setIsListening(!isListening());
          setIsPromptEditorOpen(false);
          if (!isListening()) {
            onInputChanged();
            console.log("AI RC listening stopped");
          } else {
            console.log("AI RC listening started");
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
            onInputChanged();
          }
        }}
      >
        <span class={styles.icon} role="img" aria-label="keyboard">
          ⌨️
        </span>
      </button>

      <Show when={!isRunning()}>
        <button
          class={styles.playButton}
          disabled={!pythonCode() || isLoadingPrompt()}
          onClick={() => {
            if (pythonCode()) {
              uploadAndStart(pythonCode());
            }
          }}
          title="Run Python code"
        >
          <svg
            class={styles.icon}
            width="24"
            height="24"
            viewBox="0 0 24 24"
            aria-label="play"
            fill="currentColor"
          >
            <polygon points="6,4 20,12 6,20" />
          </svg>
        </button>
      </Show>

      <Show when={isRunning()}>
        <button class={styles.stopButton} onClick={onStop} title="Stop">
          &#9632;
        </button>
      </Show>

      <div class={styles.prompt}>
        <div class={styles.promptHeader}>
          <h2>AI RC Conversation</h2>
          <button
            class={styles.clearButton}
            onClick={onClearConversation}
            title="Clear conversation"
          >
            🗑️
          </button>
          <button
            class={styles.retryButton}
            disabled={isLoadingPrompt()}
            onClick={()=>sendQuery(true)}
            title="Retry AI query"
          >
            🔄
          </button>
        </div>
        <Show when={conversation().length > 0}>
          <div class={styles.conversation}>
            <ul class={styles.conversationList}>
              {conversation().map((entry, idx) => (
                <li class={styles[entry.type]}>
                  <div class={styles.sender}>[{entry.type}]</div>&nbsp;
                  <div>{entry.message}</div>
                  <button
                    class={styles.clearButton}
                    title="Remove message"
                    onClick={() => {
                      const updated = [...conversation()];
                      updated.splice(idx, 1);
                      setConversation(updated);
                      localStorage.setItem(
                        "ai-rc-conversation",
                        JSON.stringify(updated)
                      );
                    }}
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </Show>
        {text() && <pre class={styles.promptText} innerHTML={text()}></pre>}
      </div>

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
                onInputChanged();
              }
            }}
          ></textarea>
        </div>
      )}
      {error() && (
        <div class={styles.error}>
          <h3>Error</h3>
          <button
            class={styles.closeButton}
            onClick={() => setError(undefined)}
            aria-label="Close error"
          >
            ×
          </button>
          <pre>{error()}</pre>
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

export default BlocklyAIView;


