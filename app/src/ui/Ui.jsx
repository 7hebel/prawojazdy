import { useEffect, useRef, useState } from 'react';
import React from 'react';
import ReactDOM from 'react-dom';
import { User, BookCheck, X, DoorOpen, Palette } from 'lucide-react';
import { useHotkeys } from 'react-hotkeys-hook'
import { toast, Bounce } from 'react-toastify';
import './Ui.css';


function _DepthButtonBase({ text, onClick, className, icon, ref, kbd, ...attrs }) {
  return (
    <button
      className={"ui-btn-depth " + className}
      onClick={onClick}
      ref={ref}
      {...attrs}
    >
      {kbd && <KeyboardShortcut kbd={kbd}/>}
      {icon}
      {text}
    </button>
  )
}

function _AnswerOptionTN({ answerValue, isSelected, selectSetter, ref, kbd }) {
  const text = (answerValue == "T")? "Tak" : "Nie";
  return (
    <_DepthButtonBase
      text={text}
      ref={ref}
      kbd={kbd}
      id={'possible-answer-' + answerValue}
      onClick={() => { selectSetter(answerValue) }}
      className={'answer-option ' + (isSelected? 'selected-answer' : '')}
    ></_DepthButtonBase>
  )

}

export function AnswersTN({ questionID, showData }) {
  const [selected, setSelected] = useState("");
  const optionT = useRef(null);
  const optionN = useRef(null);
  const id = 'answer-' + questionID + (showData ? '-wrong' : '');

  useHotkeys('1', () => optionT.current.click());
  useHotkeys('2', () => optionN.current.click());

  useEffect(() => {
    if (showData) { 
      setSelected(showData.selected);
      if (showData.correct == "T") {
        optionT.current.style.backgroundColor = "green";
      } else {
        optionN.current.style.backgroundColor = "green";
      }
    }
  }, [showData])

  function onSelectHandler() {
    if (!showData) return setSelected;
    return () => {}
  }

  return (
    <div 
      className='answers-tn-container'
      id={id}
      answer={selected}>
        <_AnswerOptionTN key={id + 't'} kbd="1" ref={optionT} answerValue='T' isSelected={selected=='T'} selectSetter={onSelectHandler()}/>
        <_AnswerOptionTN key={id + 'n'} kbd="2" ref={optionN} answerValue='N' isSelected={selected=='N'} selectSetter={onSelectHandler()}/>
    </div>
  )
}

function _AnswerOptionABC({ answerValue, answerContent, isSelected, selectSetter, ref, kbd }) {
  return (
    <div id={'possible-answer-' + answerValue} ref={ref} className={'abc-answer-group ' + (isSelected? "selected-abc-answer" : "") } onClick={() => {selectSetter(answerValue)}}>
      { kbd && <KeyboardShortcut kbd={kbd}/>}
      <div className='abc-answer-value'>{answerValue}</div>
      <div className='abc-answer-content'>{answerContent}</div>
    </div>
  )
}

export function AnswersABC({ questionID, answers, showData }) {
  const [selected, setSelected] = useState("");
  const id = 'answer-' + questionID + (showData? '-wrong' : '');
  const options = {
    A: useRef(null),
    B: useRef(null),
    C: useRef(null),
  }

  useHotkeys('1', () => options.A.current.click());
  useHotkeys('2', () => options.B.current.click());
  useHotkeys('3', () => options.C.current.click());

  useEffect(() => {
    if (showData) {
      setSelected(showData.selected);
      options[showData.correct].current.style.backgroundColor = "green";
    }
  }, [showData])

  function onSelectHandler() {
    if (!showData) return setSelected;
    return () => {}
  }

  return (
    <div
      className='answers-abc-container'
      id={id}
      answer={selected}
    >
      <_AnswerOptionABC key={id + 'A'} kbd="1" ref={options.A} answerValue='A' answerContent={answers['A']} isSelected={selected=='A'} selectSetter={onSelectHandler()} />
      <_AnswerOptionABC key={id + 'B'} kbd="2" ref={options.B} answerValue='B' answerContent={answers['B']} isSelected={selected=='B'} selectSetter={onSelectHandler()} />
      <_AnswerOptionABC key={id + 'C'} kbd="3" ref={options.C} answerValue='C' answerContent={answers['C']} isSelected={selected=='C'} selectSetter={onSelectHandler()} />
    </div>
  )
}


export function ButtonTimer({ text, seconds, onClick, ref, seqnum, paused, kbd }) {
  const [timer, setTimer] = useState(0);
  const [remaining, setRemaining] = useState(seconds);
  const intervalRef = useRef();

  useEffect(() => {
    if (paused) {
      clearInterval(intervalRef.current);
      return;
    }
    if (timer >= seconds) return;

    intervalRef.current = setInterval(() => {
      setTimer(prev => {
        if (prev + 1 >= seconds) {
          clearInterval(intervalRef.current);
          setTimeout(onClick, 10);
          setRemaining(0);
          return seconds;
        }
        setRemaining(seconds - (prev + 1));
        return prev + 1;
      });
    }, 1000);

    return () => clearInterval(intervalRef.current);
  }, [paused, seconds, timer, onClick]);

  const handleClick = () => {
    clearInterval(intervalRef.current);
    onClick();
  };

  return (
    <div className='button-timer-container' onClick={handleClick} ref={ref} seqnum={seqnum}>
      { kbd && <KeyboardShortcut kbd={kbd}/> }
      <span>{text}</span>
      <span className='button-timer-s'>{remaining}s</span>
      <div className='button-timer-passed' style={{ width: (timer / seconds) * 100 + "%" }}></div>
    </div>
  );
}


export function ButtonTimerSequence({ sequence, ref, index, paused }) {
  const current = sequence[index];
  return <ButtonTimer seqnum={index} ref={ref} key={index} kbd={current.kbd} text={current.text} seconds={current.seconds} paused={paused} onClick={current.onClick}></ButtonTimer>
}

export function PrimaryActionButton({ text, onClick, ref, className, id, icon, kbd }) {
  return <_DepthButtonBase ref={ref} id={id} className={'action-button ' + (className ?? '')} text={text} onClick={onClick} icon={icon} kbd={kbd}></_DepthButtonBase>
}

export function SecondaryActionButton({ text, onClick, ref, icon }) {
  return <_DepthButtonBase ref={ref} className={'action-button secondary-action'} icon={icon} text={text} onClick={onClick}></_DepthButtonBase>
}

export function FormPrimaryButton({ text, onClick, icon, id }) {
  return <button className='form-button form-primary-button' id={id} onClick={onClick}>{text}{icon}</button>
}

export function FormSecondaryButton({ text, onClick, icon, id }) {
  return <button className='form-button form-secondary-button' id={id} onClick={onClick}>{text}{icon}</button>
}

export function TopPanel({ openAccountView, openThemeView, isExam, setExam }) {
  return (
    <div className='top-panel'>
      <div className='top-panel-actions'>
        <span id='account-panel' onClick={openAccountView}><User className='top-panel-icon'/>Konto</span>
        <div className='vert-sep'></div>
        <span onClick={openThemeView}><Palette className='top-panel-icon'/>Motyw</span>
        <div className='vert-sep'></div>
        {
          isExam ? 
            <span onClick={() => {setExam(false)}}><DoorOpen className='top-panel-icon'/>Opuść egzamin</span>
          :
            <span onClick={() => {setExam(true)}}><BookCheck className='top-panel-icon'/>Nowy egzamin</span>
        }
      </div>
    </div>
  )
}

export function Modal({ title, close, icon, children }) {
  const modalRoot = document.getElementById('modal');
  const containerRef = useRef(null);
  const closeRef = useRef(null);
  const modalRef = useRef(null);

  function onClose() {
    if (modalRef && modalRef.current && close) {
      modalRef.current.classList.add('modal-transition');
      setTimeout(close, 250);
      return () => clearTimeout(timer);
    }
  }

  useEffect(() => {
    function handleEsc(event) {
      if (event.key === "Escape" || event.key === "Esc") {
        onClose();
        document.removeEventListener('keydown', handleEsc);
      }
    }

    document.addEventListener("keydown", handleEsc);

    if (modalRef && modalRef.current) {
      modalRef.current.classList.add('modal-transition');
      document.getElementsByClassName("modal-container")[0].classList.add('modal-transition')
      const timer = setTimeout(() => {
        document.getElementsByClassName("modal-container")[0].classList.remove('modal-transition')
        modalRef.current.classList.remove('modal-transition');
      }, 1);

      return () => clearTimeout(timer);
    }

  }, []);

  return ReactDOM.createPortal((
    <div className='modal-container' ref={containerRef}>
      <div className="modal" ref={modalRef}>
        <div className='modal-header'>
          <div className='row'>
            {icon && React.createElement(icon, { size: 16, color: '#ffffff50' })}
            <h1 className='modal-title'>{title}</h1>
          </div>
          {close && <X ref={closeRef} onClick={onClose} />}
        </div>
        <div className='modal-content'>
          {children}
        </div>
      </div>
    </div>
  ), modalRoot);
}

export function KeyboardShortcut({ inplace, bottom, kbd }) {
  const className = 'kbd-shortcut ' + (inplace ? 'kbd-inplace ' : '') + (bottom ? 'kbd-bottom ' : '');
  
  return (
    <span className={className}>{kbd}</span>
  )
}

export function ThemeSelector() {
  const themes = import.meta.env.VITE_THEMES.split(',');

  function select(t) {
    localStorage.setItem("theme", t);
    document.querySelector(':root').style.setProperty('--h-shift', t)
  }

  return (
    <>
      <div className='modal-sep'></div>
      <span className="settings-header">Wybierz motyw:</span>
      <div className='themes-row'>
        {
          themes.map(t => <div className='theme-selector' key={t} style={{backgroundColor: `hsl(${t}, 30%, 50%)`}} onClick={() => {select(t)}}></div>)
        }
      </div>
      <span className='sub-panel info-text'>Motyw możesz zmienić klawiszem <KeyboardShortcut inplace kbd={"m"}/></span>
    </>
  )

}


export function InputGroup({ children }) {
  return (
    <div className="input-group">{children}</div>
  )
}

export function InputLabel({ children }) {
  return (
    <p className="input-label">{children}</p>
  )
}

export function Input({ id, type = "text", className, placeholder, value, pattern, minlen, maxlen, onChange, onBlur, ref, min, max, locked, groupName }) {
  if (pattern == null && type == "number") pattern = "^\d*\.?\d*$";
  if (pattern == null && type == "email") pattern = "^[a-zA-Z0-9._%+\\-]+@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{2,}$";
  if (!className) className = '';

  return (
    <input
      id={id}
      type={type}
      className={"input-element " + className}
      placeholder={placeholder}
      pattern={pattern}
      minLength={minlen}
      maxLength={maxlen}
      onChange={onChange}
      onBlur={onBlur}
      defaultValue={value}
      ref={ref}
      step="any"
      min={min ?? undefined}
      max={max ?? undefined}
      disabled={locked}
      group={groupName}
    ></input>
  )
}

export function infoToast(message) {
  return toast.info(message, {
    theme: "dark",
    transition: Bounce,
  })
}

export function errorToast(message) {
  return toast.error(message, {
    theme: "dark",
    transition: Bounce,
  })
}

