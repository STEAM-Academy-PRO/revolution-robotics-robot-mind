import { Accessor, Setter, createEffect, onCleanup, onMount } from "solid-js";
import styles from './CodeEditor.module.css'

import { EditorView, basicSetup } from "codemirror"
import { keymap } from "@codemirror/view"
import { python } from "@codemirror/lang-python"
import { oneDarkTheme } from "@codemirror/theme-one-dark"
import {throttle} from "underscore"

function CodeEditor({ value, setValue }: { value: Accessor<string>, setValue: Setter<string> }) {

  let editorRef: HTMLDivElement;
  let editor: EditorView;

  const initVal = value()

  const saveNow = ()=>{
    const newCode = editor.state.doc.toString()
    setValue(newCode)
  }
  const throttledUpdater = throttle(saveNow, 2000)

  onMount(() => {
    // Define a custom keymap for handling the Tab key
    const myKeymap = keymap.of([{
      key: "Tab",
      run: (view) => {
        // Insert 4 spaces. You can customize this action.
        view.dispatch(view.state.replaceSelection(" "));
        return true; // Indicate that the key event has been handled
      }
    }]);
    editor = new EditorView({
      extensions: [
        basicSetup,
        python(),
        myKeymap,
        oneDarkTheme,
        EditorView.updateListener.of(throttledUpdater),
        EditorView.domEventHandlers({blur: saveNow})
      ],
      doc: value(),
      parent: editorRef

    })

  });

  onCleanup(() => {
    editor.destroy()
  })

  return <div ref={editorRef!} class={styles.editor}/>
}

export default CodeEditor