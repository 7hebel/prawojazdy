import { useEffect } from "react";
import { AnswersABC, AnswersTN } from "./Ui";
import './Quiz.css'


export function Quiz({ questionData }) {
  // questionData.index
  // questionData.question
  // questionData.answers --> "TN" / {"A": "...", "B": "...", "C": "..."}
  // questionData.media_name

  // questionData = { "question": "Jaką decyzję podejmie starosta, jeśli zostałeś zatrzymany do kontroli kierując pojazdem pomimo przedłużeniu okresu zatrzymania prawa jazdy do sześciu miesięcy za przekroczenie prędkości o więcej niż 50 km/h w obszarze  zabudowanym?", "correct_answer": "C", "media_name": "", "index": 1872, "answers": { "A": "Przedłuży okres zatrzymania o kolejne trzy miesiące.", "B": "Przedłuży okres zatrzymania o kolejne cztery miesiące.", "C": "Cofnie uprawnienie do kierowania pojazdem." } }
  questionData = { "question": "Czy w tej sytuacji masz prawo kilkukrotnie użyć sygnału dźwiękowego, zamiast zatrzymać pojazd?", "correct_answer": "Nie", "media_name": "532.D28KW_org.mp4", "index": 459, "answers": "TN" }

  const mediaType = (
    questionData.media_name.endsWith(".mp4") ? "VIDEO" :
    (
      questionData.media_name.endsWith(".jpg") ? "IMAGE" : "NOMEDIA"
    )
  )


  return (
    <main id="quiz-view">
      <header className="top-panel">
        <progress id="time-progress" value={0.23}></progress>

      </header>
      <div className="quiz-container">
        <div className="media-panel quiz-panel">
          {
            mediaType !== "NOMEDIA" &&
            <div className="media-container">
              {
                mediaType == "VIDEO" &&
                <video id="display-media" muted src={import.meta.env.VITE_API + "media/" + questionData.media_name}></video>
              }
  
              {
                mediaType == "IMAGE" &&
                <img id="display-media" src={import.meta.env.VITE_API + "media/" + questionData.media_name}></img>
              }
              <div id="media-blur" onClick={(ev) => {ev.target.remove()}}>Zapoznaj się z pytaniem</div>
            </div>
          }
        </div>
        <div className="quiz-panel">
          <span className="question-content">{questionData.question}</span>
        </div>
        <div className="answers-panel">
          {
            questionData.answers == "TN" ? 
            <AnswersTN questionID={questionData.index}></AnswersTN> :
            <AnswersABC questionID={questionData.index} answers={questionData.answers}></AnswersABC>
          }
        </div>
      </div>
    </main>
  )
}


