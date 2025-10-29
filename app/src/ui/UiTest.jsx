import { AnswersTN, AnswersABC, ButtonTimer, ButtonTimerSequence, PrimaryActionButton, SecondaryActionButton } from './Ui';
import './UiTest.css';

export default function UiTest() {
  return (
    <main id='ui-test'>
      <h1>Answers TN:</h1>
      <AnswersTN questionID={'123'}/>

      <div className='spacer'></div>

      <h1>Answers ABC:</h1>
      <AnswersABC questionID={'ABC'} answers={{
        'A': 'Zawsze, gdy widzisz pojazd poprzedzający.',
        'B': 'Zawsze, gdy istnieje możliwość oślepienia kierującego pojazdem poprzedzającym. Zawsze, gdy istnieje możliwość oślepienia kierującego pojazdem poprzedzającym. Zawsze, gdy istnieje możliwość oślepienia kierującego pojazdem poprzedzającym',
        'C': 'Zawsze, gdy widzisz pojedynczego pieszego na jezdni.',
      }}/>

      <div className='spacer'></div>

      <h1>Button timer:</h1>
      <div className='row'>
        <ButtonTimer
          text="Dalej"
          seconds={10}
          onClick={() => {}}
        />
        <ButtonTimerSequence 
          sequence={[
            {text: "Sequence element 1", seconds: 5, onClick: () => {console.log("Sequence element 1")}},
            {text: "Sequence element 2", seconds: 5, onClick: () => {console.log("Sequence element 2")}},
            {text: "Sequence element 3", seconds: 5, onClick: () => {console.log("Sequence element 3")}}
          ]}
        />
      </div>

      <div className='spacer'></div>

      <h1>Other buttons:</h1>
      <div className='row'>
        <PrimaryActionButton text="Primary action"/>
        <SecondaryActionButton text="Secondary action"/>
      </div>
    </main>
  )
}
