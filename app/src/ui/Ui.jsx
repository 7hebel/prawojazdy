import { useEffect, useRef, useState } from 'react';
import React from 'react';
import ReactDOM from 'react-dom';
import './Ui.css';
import { User, BookCheck, X } from 'lucide-react';

function _DepthButtonBase({ text, onClick, className, icon, ref, ...attrs }) {
  return (
    <button
      className={"ui-btn-depth " + className}
      onClick={onClick}
      ref={ref}
      {...attrs}
    >
      {text}
      {icon}
    </button>
  )
}

function _AnswerOptionTN({ answerValue, isSelected, selectSetter, ref }) {
  const text = (answerValue == "T")? "Tak" : "Nie";
  return (
    <_DepthButtonBase
      text={text}
      ref={ref}
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
        <_AnswerOptionTN key={id + 't'} ref={optionT} answerValue='T' isSelected={selected=='T'} selectSetter={onSelectHandler()}/>
        <_AnswerOptionTN key={id + 'n'} ref={optionN} answerValue='N' isSelected={selected=='N'} selectSetter={onSelectHandler()}/>
    </div>
  )
}

function _AnswerOptionABC({ answerValue, answerContent, isSelected, selectSetter, ref }) {
  return (
    <div id={'possible-answer-' + answerValue} ref={ref} className={'abc-answer-group ' + (isSelected? "selected-abc-answer" : "") } onClick={() => {selectSetter(answerValue)}}>
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
      <_AnswerOptionABC key={id + 'A'} ref={options.A} answerValue='A' answerContent={answers['A']} isSelected={selected=='A'} selectSetter={onSelectHandler()} />
      <_AnswerOptionABC key={id + 'B'} ref={options.B} answerValue='B' answerContent={answers['B']} isSelected={selected=='B'} selectSetter={onSelectHandler()} />
      <_AnswerOptionABC key={id + 'C'} ref={options.C} answerValue='C' answerContent={answers['C']} isSelected={selected=='C'} selectSetter={onSelectHandler()} />
    </div>
  )
}


export function ButtonTimer({ text, seconds, onClick, ref, seqnum, paused }) {
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
      <span>{text}</span>
      <span className='button-timer-s'>{remaining}s</span>
      <div className='button-timer-passed' style={{ width: (timer / seconds) * 100 + "%" }}></div>
    </div>
  );
}


export function ButtonTimerSequence({ sequence, ref, index, paused }) {
  const current = sequence[index];
  return <ButtonTimer seqnum={index} ref={ref} key={index} text={current.text} seconds={current.seconds} paused={paused} onClick={current.onClick}></ButtonTimer>
}

export function PrimaryActionButton({ text, onClick, ref, className, id, icon }) {
  return <_DepthButtonBase ref={ref} id={id} className={'action-button ' + (className ?? '')} text={text} onClick={onClick} icon={icon}></_DepthButtonBase>
}

export function SecondaryActionButton({ text, onClick, ref }) {
  return <_DepthButtonBase ref={ref} className={'action-button secondary-action'} text={text} onClick={onClick}></_DepthButtonBase>
}

export function TopPanel({ startExam }) {
  return (
    <div className='top-panel'>
      <span></span>
      <div className='top-panel-actions'>
        <span><User className='top-panel-icon'/>Konto</span>
        <div className='vert-sep'></div>
        <span onClick={startExam}><BookCheck className='top-panel-icon'/>Nowy egzamin</span>
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

