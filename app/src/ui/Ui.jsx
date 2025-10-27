import { useState } from 'react';
import './Ui.css';


// Answer: radio select -- Tak/Nie/abc
// ui:
// ButtonPrimary
// ButtonSecondary
// ButtonTertiary


// testy w playwrighcie
// 3 logi, 3 metryki, 3 trace'y  --  zastosowania LGTM 
// screeny z przykładów

function _AnswerOptionTF({answerType: answerValue, keyboardShortcut, isSelected, selectSetter}) {
  if (answerValue !== "T" && answerValue !== "F") {
    throw new Error(`_AnswerOptionTF::answerType must be either 'T' or 'F', not '${answerValue}'`)
  }

  function onSelect() {
    selectSetter(answerValue)
  }

  const text = (answerValue == "T")? "Prawda" : "Fałsz";

  return (
    <div 
      className='answer-option-container'
      isSelected={Number(isSelected)}
      onClick={onSelect}
      >
        {text}
    </div>
  )

}

export function AnswersTF({ questionID }) {
  const [selected, setSelected] = useState("");

  return (
    <div 
      className='answers-tf-container'
      id={'answer-' + questionID}
      answer={selected}
      >

        <_AnswerOptionTF answerType={'T'}/>
        <_AnswerOptionTF answerType={'F'}/>

    </div>
  )
}
