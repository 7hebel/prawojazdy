import { AnswersTN, AnswersABC } from './Ui';
import './UiTest.css';

export default function UiTest() {
  return (
    <>
      <h1>Answers TN:</h1>
      <AnswersTN questionID={'123'}/>

      <div className='spacer'></div>

      <h1>Answers ABC:</h1>
      <AnswersABC questionID={'ABC'} answers={{
        'A': 'Zawsze, gdy widzisz pojazd poprzedzający.',
        'B': 'Zawsze, gdy istnieje możliwość oślepienia kierującego pojazdem poprzedzającym. Zawsze, gdy istnieje możliwość oślepienia kierującego pojazdem poprzedzającym. Zawsze, gdy istnieje możliwość oślepienia kierującego pojazdem poprzedzającym',
        'C': 'Zawsze, gdy widzisz pojedynczego pieszego na jezdni.',
      }}/>
    </>
  )
}
