import { useRef, useState } from 'react';
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

