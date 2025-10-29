import { useEffect, useRef, useState } from 'react';
import './Ui.css';


function _DepthButtonBase({ text, onClick, className, ...attrs }) {
  return (
    <button
      className={"ui-btn-depth " + className}
      onClick={onClick}
      {...attrs}
    >
      {text}
    </button>
  )
}



function _AnswerOptionTN({ answerValue, isSelected, selectSetter }) {
  const text = (answerValue == "T")? "Tak" : "Nie";
  return (
    <_DepthButtonBase
      text={text}
      onClick={() => { selectSetter(answerValue) }}
      className={'answer-option ' + (isSelected? 'selected-answer' : '')}
    ></_DepthButtonBase>
  )

}

export function AnswersTN({ questionID }) {
  const [selected, setSelected] = useState("");

  return (
    <div 
      className='answers-tn-container'
      id={'answer-' + questionID}
      answer={selected}>
        <_AnswerOptionTN answerValue='T' isSelected={selected=='T'} selectSetter={setSelected}/>
        <_AnswerOptionTN answerValue='N' isSelected={selected=='N'} selectSetter={setSelected}/>
    </div>
  )
}



function _AnswerOptionABC({ answerValue, answerContent, isSelected, selectSetter }) {
  return (
    <div className={'abc-answer-group ' + (isSelected? "selected-abc-answer" : "") } onClick={() => {selectSetter(answerValue)}}>
      <div className='abc-answer-value'>{answerValue}</div>
      <div className='abc-answer-content'>{answerContent}</div>
    </div>
  )
}

export function AnswersABC({ questionID, answers }) {
  const [selected, setSelected] = useState("");

  return (
    <div
      className='answers-abc-container'
      id={'answer-' + questionID}
      answer={selected}
    >
      <_AnswerOptionABC answerValue='A' answerContent={answers['A']} isSelected={selected=='A'} selectSetter={setSelected} />
      <_AnswerOptionABC answerValue='B' answerContent={answers['B']} isSelected={selected=='B'} selectSetter={setSelected} />
      <_AnswerOptionABC answerValue='C' answerContent={answers['C']} isSelected={selected=='C'} selectSetter={setSelected} />
    </div>
  )
}


export function ButtonTimer({ text, seconds, onClick, ref, seqnum }) {
  const [timer, setTimer] = useState(0); 
  const [remaining, setRemaining] = useState(seconds);
  const timeoutsRef = useRef([]);

  useEffect(() => {
    timeoutsRef.current = [];
    for (let i = 1; i <= seconds; i++) {
      const id = setTimeout(() => {
        setTimer(i);
        setRemaining(seconds - i);
        if (seconds - i === 0) setTimeout(onClick, 10);
      }, 1000 * i);
      timeoutsRef.current.push(id);
    }
    return () => {
      timeoutsRef.current.forEach(clearTimeout);
    };
  }, [seconds, onClick]);

  const handleClick = () => {
    timeoutsRef.current.forEach(clearTimeout);
    onClick();
  };

  return (
    <div className='button-timer-container' onClick={handleClick} ref={ref} seqnum={seqnum} >
      <span>{text}</span>
      <span className='button-timer-s'>{remaining}s</span>
      <div className='button-timer-passed' style={{ width: (timer / seconds) * 100 + "%" }}></div>
    </div>
  )
}

export function ButtonTimerSequence({ sequence, ref }) {
  const [seqEl, setSeqEl] = useState(0);
  
  const current = sequence[seqEl];
  const onSeqClick = () => {
    if (seqEl < sequence.length - 1) setSeqEl(e => e + 1);
    if (current.onClick) current.onClick();
  }
  
  return <ButtonTimer seqnum={seqEl} ref={ref} key={seqEl} text={current.text} seconds={current.seconds} onClick={onSeqClick}></ButtonTimer>
}

