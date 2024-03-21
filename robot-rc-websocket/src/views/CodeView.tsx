import { createSignal, createEffect, Accessor, Setter, For, Show, createMemo } from 'solid-js'

import styles from './CodeEditor.module.css'

import { RobotMessage } from '../utils/Communicator';
import { uploadConfig } from '../utils/commands';
import { DriveMode, Program, scriptBindings, currentConfig, driveMode, handleDriveChange, programs, setScriptBindings, setPrograms, scriptBindingTargets } from '../utils/Config';
import CodeEditor from './CodeEditor';
import { BlocklyView } from './BlocklyView';
import { conn } from '../settings';


function CodeView() {

  const [edited, setEdited] = createSignal<Program | null>(null)
  const [editedCode, setEditedCode] = createSignal<string>('')
  const [editedIndex, setEditedIndex] = createSignal<number | null>(null);
  const [editedName, setEditedName] = createSignal<string>('')
  const [tab, setTab] = createSignal<string>('python');


  const addProgram = () => {
    const newProgramList = programs().slice()
    const newProgram = { name: String(programs().length + 1), code: "robot.led.set(leds=[1,2,3,4,5,6,7,8,9,10,11,12], color='#0000ff')\n\n" }
    newProgramList.push(newProgram)
    setEdited(newProgram)
    setPrograms(newProgramList)
  }

  const deleteProgram = () => {
    if (editedCode()){
      if (!confirm('Sure delete?')) { return }
    }
    const newProgramList = programs().slice()
    const editedInd = editedIndex()
    if (!editedInd && editedInd !== 0) { return }
    newProgramList.splice(editedInd, 1)
    setPrograms(newProgramList)
    setEdited(null)
  }

  createEffect(() => {
    setEditedCode(edited()?.code || '')
    setEditedName(edited()?.name || '')
  })

  const saveCode = (code: string) => {
    setEditedCode(code)
    saveEdited()
    const newProgramList = programs().slice()
    const editedInd = editedIndex()
    console.log('save')
    if (!editedInd && editedInd !== 0) { return }
    newProgramList[editedInd] = Object.assign({}, edited())
    setPrograms(newProgramList)
    console.log(newProgramList)
  }

  const saveEdited = () => {
    const current = edited()
    if (current !== null) {
      current.code = editedCode()
      current.name = editedName()
    }
  }

  const toggleBinding = (binding: string) => {
    const newBindings = Object.assign({}, scriptBindings())
    if (scriptBindings()[binding]) {
      newBindings[binding] = ''
    } else {
      newBindings[binding] = editedName()
    }
    setScriptBindings(newBindings)
  }


  return (
    <div >
      <div class={styles.codeEditor}>
        <div class={styles.column}>
          <div>

            <h4>Programs</h4>
            <div>
              <For each={programs()}>{(program, i) =>
                <div class={styles.clickable} classList={{ [styles.active]: editedIndex() === i() }} onClick={() => {
                  setEdited(null)
                  setEdited(program)
                  setEditedIndex(i)
                }}>{String(i() + 1)} - {program.name}</div>
              }</For>
              <a class={styles.clickable} onClick={addProgram}>+ Add</a>
            </div>
            <div>
              <p>Joystick mode</p>
              <select value={driveMode()} onChange={handleDriveChange}>
                <For each={Object.values(DriveMode)}>{(mode) =>
                  <option value={mode}>{mode}</option>
                }</For>
              </select>
            </div>
          </div>

        </div>
        <Show when={edited() !== null}>
          <div>
            <div class={styles.header}>
              <a onClick={() => setTab('python')} class={styles.clickable}>python</a>
              <a onClick={() => setTab('blockly')} class={styles.clickable}>blockly</a>
              <a onClick={() => deleteProgram()} class={styles.clickable}>DELETE</a>
              <div class={styles.assignments}></div>
              <a>Assignments:</a>
              <For each={scriptBindingTargets}>{(binding: string) =>
                <a class={styles.clickable}
                  classList={{
                    [styles.active]: Boolean(scriptBindings()[binding] === editedName())
                  }}
                  onClick={() => {
                    toggleBinding(binding)
                    console.warn(binding)
                  }} >{binding}</a>
              }
              </For>
            </div>

            <div class={styles.editorWrapper}>
              <div>
                Program Name: <input type="text" value={editedName()} onInput={(e) => { setEditedName(e.target.value); saveEdited() }} />
              </div>
              <Show when={tab() === 'python'}>
                <CodeEditor value={editedCode} setValue={saveCode}></CodeEditor>
              </Show>
              <Show when={tab() === 'blockly'}>
                <BlocklyView onSave={setEditedCode} />
              </Show>
            </div>
          </div>
        </Show>

      </div>
    </div>
  );
}

export default CodeView

