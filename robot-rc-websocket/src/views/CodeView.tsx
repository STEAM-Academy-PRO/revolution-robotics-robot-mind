import { createSignal, createEffect,For, Show, onCleanup } from 'solid-js'

import styles from './CodeEditor.module.css'

import { DriveMode, Program, scriptBindings, driveMode, handleDriveChange, programs, setScriptBindings, setPrograms, scriptBindingTargets } from '../utils/Config';
import CodeEditor from './CodeEditor';
import { BlocklyView } from './BlocklyView';
import defaultBlocklyXml from './utils/default-xml';


function CodeView() {

  const [edited, setEdited] = createSignal<Program | null>(null)
  const [editedCode, setEditedCode] = createSignal<string>('')
  const [editedXml, setEditedXml] = createSignal<string>('')
  const [editedIndex, setEditedIndex] = createSignal<number | null>(null);
  const [editedName, setEditedName] = createSignal<string>('')
  const [tab, setTab] = createSignal<string>('blockly');


  const addProgram = () => {
    const newProgramList = programs().slice()
    const newProgram = { name: String(programs().length + 1), python: "robot.led.set(leds=[1,2,3,4,5,6,7,8,9,10,11,12], color='#0000ff')\n\n", xml: defaultBlocklyXml }
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
    // setEditedCode(edited()?.python || '')
    setEditedName(edited()?.name || '')
  })

  const saveCode = (python: string, xml: string) => {
    setEditedCode(python)
    setEditedXml(xml)
    saveEdited()
    const newProgramList = programs().slice()
    const editedInd = editedIndex()
    console.warn('save', python)
    if (!editedInd && editedInd !== 0) { return }
    newProgramList[editedInd] = Object.assign({}, edited())
    setPrograms(newProgramList)
    // console.log(newProgramList)
  }

  const saveEdited = () => {
    const current = edited()
    if (current !== null) {
      current.python = editedCode()
      current.xml = editedXml()
      current.name = editedName()
      // console.log('current.xml', current.xml)
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

  onCleanup(() => {
    
    if (edited() !== null) {
      console.log('oncleanup', edited())
      saveEdited()
      const newProgramList = programs().slice()
      const editedInd = editedIndex()
      if (editedInd !== null) {
        newProgramList[editedInd] = Object.assign({}, edited())
        setPrograms(newProgramList)
      }
    }
  })


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
                <CodeEditor value={editedCode} setValue={(python) => saveCode(python, '')}></CodeEditor>
              </Show>
              <Show when={tab() === 'blockly'}>
                <BlocklyView onSave={(xml, python) => saveCode(python, xml)} xml={edited()?.xml || ''} />
              </Show>
            </div>
          </div>
        </Show>

      </div>
    </div>
  );
}

export default CodeView

