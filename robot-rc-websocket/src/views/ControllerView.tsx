import { createSignal, createEffect, createMemo, onCleanup, Accessor, Setter } from 'solid-js'
import { RobotMessage, SocketWrapper } from '../utils/Communicator';
import { Position } from '../utils/Position';
import { mapAnalogNormal, toByte } from '../utils/mapping';
import { Joystick } from '../components/Joystick';

export default function ControllerView({
  conn, isActive }: { conn: Accessor<SocketWrapper|null>, isActive: Accessor<boolean> }) {

  const buttons = [0, 1, 2, 3].map((i)=>{
      let [get, set] = createSignal<boolean>(false)
      return {get, set}
  })

  const position = new Position()

  let i = 0


  let last = {x: 0, y: 0}


  // let doSendMove = false
  // We have to send the control messages whenever we uploaded it, or else it resets configuration state.
  // Try uncommenting the lines with doSendMove in them. The first time it stops receiving the messages
  // on the robot the state resets to not configured.

  const interval = setInterval(() => {
    // if (!on){ return }
    // const controlMessage
    // doSendMove = Boolean(last.x || last.y || (position.x() || position.y()))

    if (!isActive()){ return }

    last.x = position.x()
    last.y = position.y()

    // if (!doSendMove) { return }

    const buttonByte = toByte(buttons.map((b)=>b.get()))
    // console.warn(buttonByte)

    const ctrlArray = new Uint8Array([
      i++ % 127, // keepalive - no need to change this as it's bluetooth specific
      mapAnalogNormal(position.x()), // UInt8, left-right analog, value range: 0-255
      mapAnalogNormal(position.y()), // UInt8, bottom-top analog, value range: 0-255

      0, // unused analog
      0, // unused analog
      0, // unused analog
      0, // unused analog


      0, // Reserved
      0, // Reserved
      0, // Reserved
      0, // Reserved

      buttonByte, // UInt8, button group 1, 1 button per bit
      0, // UInt8, button group 2, 1 button per bit
      0, // UInt8, button group 3, 1 button per bit
      0, // UInt8, button group 4, 1 button per bit

    ])

    isActive() && conn()?.send(RobotMessage.control, ctrlArray)
  }, 100)

  onCleanup(() => {
    clearInterval(interval)
  })


  return (
      <div>
        <h1>Controller</h1>
        <Joystick position={position}></Joystick>
        <Buttons list={buttons.map((b)=>b.set)}/>
        {/* {buttons.map((b)=>b.get()?<>1</>:<>0</>)} */}
    </div>
  );
}


function Button({label, setter}: {label: string, setter: Setter<boolean>}){
  return <button onMouseDown={()=>setter(true)} onMouseUp={()=>setter(false)}>{label}</button>
}


function Buttons({list}: {list: Setter<boolean>[]}){
  return list.map((b, i)=><Button label={String(i)} setter={b}/>)
}