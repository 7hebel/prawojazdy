import { useEffect, useRef } from "react";
import { AnswersABC, AnswersTN, ButtonTimerSequence } from "./Ui";
import './Quiz.css'


export function Quiz({ questionData, isExamMode }) {
  // questionData.index
  // questionData.question
  // questionData.answers --> "TN" / {"A": "...", "B": "...", "C": "..."}
  // questionData.media_name
  // questionData.points
  // questionData.category

  // questionData = { "question": "Jaką decyzję podejmie starosta, jeśli zostałeś zatrzymany do kontroli kierując pojazdem pomimo przedłużeniu okresu zatrzymania prawa jazdy do sześciu miesięcy za przekroczenie prędkości o więcej niż 50 km/h w obszarze  zabudowanym?", "correct_answer": "C", "media_name": "", "index": 1872, "answers": { "A": "Przedłuży okres zatrzymania o kolejne trzy miesiące.", "B": "Przedłuży okres zatrzymania o kolejne cztery miesiące.", "C": "Cofnie uprawnienie do kierowania pojazdem." }, "points": 2, "category": "SPECJALISTYCZNY" }
  questionData = { "question": "Czy w tej sytuacji masz prawo kilkukrotnie użyć sygnału dźwiękowego, zamiast zatrzymać pojazd?", "correct_answer": "Nie", "media_name": "532.D28KW_org.mp4", "index": 459, "answers": "TN", "points": 1, "category": "PODSTAWOWY" }

  const mediaType = (
    questionData.media_name.endsWith(".mp4") ? "VIDEO" :
    (
      questionData.media_name.endsWith(".jpg") ? "IMAGE" : "NOMEDIA"
    )
  )
  const mediaSrc = (mediaType != "NOMEDIA") ? import.meta.env.VITE_API + "media/" + questionData.media_name : "nomedia.png"

  let actionButtonsSequence;
  if (questionData.category == "PODSTAWOWY") {
    actionButtonsSequence = [
      { text: "Start", seconds: 20, onClick: () => { startBasicQuestion() }},
      { text: "Dalej", seconds: 15, onClick: () => {} },
    ]
  } else {
    actionButtonsSequence = [
      { text: "Dalej", seconds: 50, onClick: () => {} },
    ]
  }

  const mediablur = useRef(null);
  const actionbtn = useRef(null);

  function startBasicQuestion(ev) {
    if (ev?.target.id == "media-blur") {
      if (actionbtn.current.getAttribute("seqnum") == "0") actionbtn.current.click();
    }
    if (mediaType == "VIDEO") {
      const videoMedia = document.getElementById("display-media");

      videoMedia.play()
      .then(e => {
        mediablur.current.remove();
      })
      .catch(e => {
        mediablur.current.textContent = "Rozpocznij odtwarzanie...";
        mediablur.current.removeEventListener('click', startBasicQuestion);
        mediablur.current.addEventListener('click', () => {
          videoMedia.play();
          mediablur.current.remove();
          console.warn("Started playback using fallback solution...")
        })
        
        console.warn("failed to play media...")
      });
    } else {
      mediablur.current.remove();
    }
  }

  return (
    <main id="quiz-view">
      <div className="quiz-container">
        <div className="panels-row">
          <div className="quiz-panel media-panel">
            
            <div className="media-container">
              {
                mediaType == "VIDEO" &&
                <video id="display-media" muted playsInline src={mediaSrc}></video>
              }
  
              {
                (mediaType == "IMAGE" || mediaType == "NOMEDIA") &&
                <img id="display-media" src={mediaSrc}></img>
              }
              {
                questionData.category == "PODSTAWOWY" &&
                <div ref={mediablur} id="media-blur" onClick={startBasicQuestion}>Zapoznaj się z pytaniem</div>
              }
            </div>
            
          </div>
          <div className="quiz-panel actions-panel">
            <div className="metadata-row">
              <span>Zestaw: <span className="important-text">{questionData.category.toLowerCase()}</span></span>
              <span><span className="important-text">{questionData.points}</span>p.</span>
            </div>
            <ButtonTimerSequence ref={actionbtn} sequence={actionButtonsSequence}></ButtonTimerSequence>
          </div>
        </div>
        <div className="quiz-panel question-panel">
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


