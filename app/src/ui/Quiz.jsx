import { useEffect, useRef, useState } from "react";
import { AnswersABC, AnswersTN, ButtonTimerSequence, PrimaryActionButton } from "./Ui";
import './Quiz.css'


export function Quiz({ questionData, isExamMode }) {
  // questionData = { "question": "Jaką decyzję podejmie starosta, jeśli zostałeś zatrzymany do kontroli kierując pojazdem pomimo przedłużeniu okresu zatrzymania prawa jazdy do sześciu miesięcy za przekroczenie prędkości o więcej niż 50 km/h w obszarze  zabudowanym?", "correct_answer": "C", "media_name": "", "index": 1872, "answers": { "A": "Przedłuży okres zatrzymania o kolejne trzy miesiące.", "B": "Przedłuży okres zatrzymania o kolejne cztery miesiące.", "C": "Cofnie uprawnienie do kierowania pojazdem." }, "points": 2, "category": "SPECJALISTYCZNY" }
  questionData = { "question": "Czy w tej sytuacji masz prawo kilkukrotnie użyć sygnału dźwiękowego, zamiast zatrzymać pojazd?", "correct_answer": "Nie", "media_name": "532.D28KW_org.mp4", "index": 459, "answers": "TN", "points": 1, "category": "PODSTAWOWY" }
  // isExamMode=true;

  const mediaType = (
    questionData.media_name.endsWith(".mp4") ? "VIDEO" :
    (
      questionData.media_name.endsWith(".jpg") ? "IMAGE" : "NOMEDIA"
    )
  )
  const mediaSrc = (mediaType != "NOMEDIA") ? import.meta.env.VITE_API + "media/" + questionData.media_name : "nomedia.png"

  let actionButtonsSequence;
  if (isExamMode) {
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
  }

  const mediaelement = useRef(null);
  const mediablur = useRef(null);
  const actionbtn = useRef(null);

  function unblurMedia() {
    mediablur.current.style.opacity = 0;
    setTimeout(() => {mediablur.current.remove()}, 500)
  }

  function mediaBlurAsPlayBtn() {
    mediablur.current.textContent = "Rozpocznij odtwarzanie...";
    mediablur.current.removeEventListener('click', startBasicQuestion);
    mediablur.current.addEventListener('click', () => {
      mediaelement.current.play();
      unblurMedia();
    })
  }

  useEffect(() => {
    if (!isExamMode) {
      if (navigator.getAutoplayPolicy("mediaelement") === "disallowed") {
        mediaBlurAsPlayBtn();
      } else {
        unblurMedia();
      }
      mediaelement.current.addEventListener("click", () => { mediaelement.current.play(); })
    } 
  }, [])

  const [seqBtnIndex, setSeqBtnIndex] = useState(0);

  function startBasicQuestion(ev) {
    if (ev?.target.id == "media-blur") {
      if (actionbtn.current.getAttribute("seqnum") == "0") actionbtn.current.click();
    }
    if (mediaType == "VIDEO") {
      mediaelement.current.addEventListener("ended", () => { setSeqBtnIndex(1) })
      mediaelement.current.play()
      .then(e => {
        unblurMedia();
      })
      .catch(e => {
        mediaBlurAsPlayBtn();
        console.warn("failed to play media...")
      });
    } else {
      unblurMedia();
      setSeqBtnIndex(1);
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
                <video id="display-media" ref={mediaelement} muted playsInline src={mediaSrc}></video>
              }
  
              {
                (mediaType == "IMAGE" || mediaType == "NOMEDIA") &&
                <img id="display-media" ref={mediaelement} src={mediaSrc}></img>
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
              <span>Tryb: <span className="important-text">{(isExamMode) ? 'egzamin' : 'nauka'}</span></span>
              <span>Waga: <span className="important-text">{questionData.points}pkt.</span></span>
            </div>
            {
              isExamMode? 
                <ButtonTimerSequence ref={actionbtn} sequence={actionButtonsSequence} index={seqBtnIndex}></ButtonTimerSequence>
              :
                <PrimaryActionButton ref={actionbtn} text="Dalej"></PrimaryActionButton>
            }
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


