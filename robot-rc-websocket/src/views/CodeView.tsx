import { createSignal, createEffect, For, Show, onCleanup } from "solid-js";

import styles from "./CodeEditor.module.css";

import {
  DriveMode,
  Program,
  scriptBindings,
  driveMode,
  handleDriveChange,
  programs,
  setScriptBindings,
  setPrograms,
  scriptBindingTargets,
} from "../utils/Config";
import CodeEditor from "./CodeEditor";
import { BlocklyView } from "./BlocklyView";
import defaultBlocklyXml from "../utils/default-xml";

function CodeView() {
  const [editedId, setEditedId] = createSignal<number | null>(null);

  const addProgram = () => {
    const newProgram = {
      id: programs().length,
      name: String(programs().length + 1),
      python:
        "robot.led.set(leds=[1,2,3,4,5,6,7,8,9,10,11,12], color='#0000ff')\n\n",
      xml: defaultBlocklyXml,
    };
    setPrograms([...programs(), newProgram]);
    loadEditedProgram(newProgram);
  };

  const deleteProgram = () => {
    if (!confirm("Sure delete?")) {
      return;
    }
    setPrograms(programs().filter((o) => o.id !== editedId()));
    setEditedId(null);
  };

  const selectedProgram = () =>
    programs().find((item) => item.id === editedId()) ?? null;


  const toggleBinding = (binding: string) => {
    const newBindings = Object.assign({}, scriptBindings());
    if (scriptBindings()[binding]) {
      newBindings[binding] = "";
    } else {
      newBindings[binding] = selectedProgram()!.name;
    }
    setScriptBindings(newBindings);
  };

  const loadEditedProgram = (program: Program) => {
    setEditedId(null);
    setEditedId(program.id);
  };

  const onSave = (program: Program) => {
    const updatedPrograms = programs().map((p) =>
      p.id === program.id ? program : p
    );
    updatedPrograms.forEach((p, i) => {
      if (!p.name){
        console.warn(`Program ${p.id} has no name, setting to default!!!`, p);
        // debugger
        p.name = String(i + 1);
      }
    }
    )
    setPrograms(updatedPrograms);
  }

  return (
    <div>
    <div class={styles.codeEditor}>
      <div class={styles.column}>
        <div>
          <h4>Programs</h4>
          <div>
            <For each={programs()}>
              {(program, i) => (
                <div
                  class={styles.clickable}
                  classList={{ [styles.active]: editedId() === program.id }}
                  onClick={() => {
                    loadEditedProgram(program);
                  }}
                >
                  {String(i() + 1)} - {program.name}
                </div>
              )}
            </For>
            <a class={styles.clickable} onClick={addProgram}>
              + Add
            </a>
          </div>
          <div>
            <p>Joystick mode</p>
            <select value={driveMode()} onChange={handleDriveChange}>
              <For each={Object.values(DriveMode)}>
                {(mode) => <option value={mode}>{mode}</option>}
              </For>
            </select>
          </div>
        </div>
      </div>

      <Show when={selectedProgram()}>
        <div class={styles.editor}>
          <div class={styles.header}>
            <a onClick={() => deleteProgram()} class={styles.clickable}>
              DELETE
            </a>
            <div class={styles.assignments}></div>
            <a>Assignments:</a>
            <For each={scriptBindingTargets}>
              {(binding: string) => (
                <a
                  class={styles.clickable}
                  classList={{
                    [styles.active]: Boolean(
                      scriptBindings()[binding] === selectedProgram()!.name
                    ),
                  }}
                  onClick={() => {
                    toggleBinding(binding);
                    console.warn(binding);
                  }}
                >
                  {binding}
                </a>
              )}
            </For>
          </div>
          <div class={styles.editorContent}>
            <Edited
              program={selectedProgram()!}
              onSave={onSave}></Edited>
          </div>
        </div>
      </Show>
    </div>
    </div>
  );
}

function Edited(props: {program: Program, onSave: (program: Program) => void}) {
  const [editedCode, setEditedCode] = createSignal<string>(props.program.python || "");
  const [editedXml, setEditedXml] = createSignal<string>(props.program.xml || "");
  const [editedName, setEditedName] = createSignal<string>(props.program.name || "");
  const [tab, setTab] = createSignal<string>("python");

  const onSave = (name: string, python: string, xml: string) => {
    const updatedProgram = {
      ...props.program,
      name: name,
      python: python,
      xml: xml,
    };
    props.onSave(updatedProgram);
    setEditedCode(python);
    setEditedXml(xml);
    setEditedName(name);
  };
  return (
    <div class={styles.editorWrapper}>
      <div>
        Program Name:{" "}
        <input
          type="text"
          value={editedName()}
          onInput={(e) => onSave(e.target.value, editedCode(), editedXml())}
        />
        <div class={styles.header}>
              <a
                onClick={() => setTab("blockly")}
                classList={{
                  [styles.clickable]: true,
                  [styles.activeTab]: tab() === "blockly",
                }}
              >
                blockly
              </a>
              <a
                onClick={() => setTab("python")}
                classList={{
                  [styles.clickable]: true,
                  [styles.activeTab]: tab() === "python",
                }}
              >
                python
              </a>
          </div>
      </div>
      {/* <Show when={false && tab() === "blockly"}>
        <BlocklyView
          onSave={(xml, python) => onSave(editedName(), python, xml)}
          xml={props.program.xml || ""}
        />
      </Show> */}
      {/* This breaks everything, for now, it's just blockly */}
      <Show when={tab() === 'python'}>
        <CodeEditor value={editedCode} setValue={(python) => onSave(editedName(), python, props.program.xml || '')}></CodeEditor>
      </Show>
    </div>
  );
}

export default CodeView;
