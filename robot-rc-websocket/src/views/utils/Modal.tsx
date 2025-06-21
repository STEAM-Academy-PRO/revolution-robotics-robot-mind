import { Show } from 'solid-js';

type ModalProps = {
    isOpen: boolean;
    onClose: () => void;
    children: any;
};

export default function Modal(props: ModalProps) {
    return (
        <Show when={props.isOpen}>
            <div style={overlayStyle}>
                <div style={modalStyle}>
                    <button style={closeButtonStyle} onClick={props.onClose}>
                        &times;
                    </button>
                    {props.children}
                </div>
            </div>
        </Show>
    );
}

const overlayStyle = `
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
`;

const modalStyle = `
    background: #fff;
    padding: 24px;
    border-radius: 8px;
    min-width: 300px;
    position: relative;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
`;

const closeButtonStyle = `
    position: absolute;
    top: 8px;
    right: 12px;
    background: transparent;
    border: none;
    font-size: 24px;
    cursor: pointer;
`;
