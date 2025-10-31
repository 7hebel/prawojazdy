import { useEffect, useRef, useState } from "react";
import { AnswersABC, AnswersTN, ButtonTimerSequence, PrimaryActionButton } from "./Ui";
import './Quiz.css'

function NextQuestionTimeoutAnimation() {
  const barRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    containerRef.current.style.height = "0px";
    barRef.current.style.width = "0%";
    void barRef.current.offsetWidth;

    containerRef.current.style.height = "12px";
    barRef.current.style.width = "102%";

    const timeout = setTimeout(() => {
      containerRef.current.style.height = "0px";
    }, 2500);

    return () => clearTimeout(timeout);
  }, [])

  return (
    <div ref={containerRef} className="next-question-timeout-container" style={{height: 0}}>
      <div ref={barRef} className="next-question-timeout-line" style={{width: 0}}></div>
    </div>
  )
}

function PracticeProgress({ questionNumber, hardQuestions }) {
  const totalQuestions = import.meta.env.VITE_TOTAL_QUESTIONS;
  const progressPercentage = Math.round((questionNumber / totalQuestions) * 100);
  const hardPercentage = Math.round((hardQuestions / totalQuestions) * 100);

  return (
    <div className="practice-progress">
      <div className="practice-progress-data">
        <span className="important-text">{progressPercentage}%</span>
        <span>
          <span className="important-text">{questionNumber}</span>
          /{totalQuestions}
        </span>
      </div>
      <div className="practice-progress-bar-container">
        <div className="practice-progress-bar-fill" style={{ width: progressPercentage + "%"}}></div>
        <div className="practice-progress-bar-fill-hard" style={{width: hardPercentage + "%"}}></div>
      </div>
      <span className="practice-progress-hard-count">Błędy: {hardQuestions}</span>
    </div>
  )
}


export function Quiz({ questionData, isExamMode, onContinue }) {
  if (questionData == null) { return <h1>no data</h1> }

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
        { text: "Dalej", seconds: 15, onClick: () => { onContinue(getSelectedAnswer()) } },
      ]
    } else {
      actionButtonsSequence = [
        { text: "Dalej", seconds: 50, onClick: () => { onContinue(getSelectedAnswer()) } },
      ]
    }
  }

  const mediaelement = useRef(null);
  const mediablur = useRef(null);
  const actionbtn = useRef(null);

  function unblurMedia() {
    if (mediablur.current) {
      mediablur.current.style.opacity = 0;
      setTimeout(() => {mediablur.current.remove()}, 500)
    }
  }

  function mediaBlurAsPlayBtn() {
    if (!mediablur.current) return;
    mediablur.current.textContent = "Rozpocznij odtwarzanie...";
    mediablur.current.removeEventListener('click', startBasicQuestion);
    mediablur.current.addEventListener('click', () => {
      mediaelement.current.play();
      unblurMedia();
    })
  }

  function getSelectedAnswer() {
    return document.getElementById("answer-" + questionData.index).getAttribute("answer");
  }

  useEffect(() => {
    if (!isExamMode) {
      if (mediaType == "IMAGE") {
        unblurMedia();
        return
      }
      
      if (typeof navigator.getAutoplayPolicy === 'function') { // Firefox
        if (navigator.getAutoplayPolicy("mediaelement") === "disallowed") {
          mediaBlurAsPlayBtn();
        } else {
          unblurMedia();
        }
      } else { // Chrome
        try {
          mediaelement.current.play();
          unblurMedia();
        } catch {
          mediaBlurAsPlayBtn();
        }
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

  function onPracticeNext(ev) {
    if (getSelectedAnswer().length) {
      onContinue(getSelectedAnswer());
    } else {
      ev.target.classList.add("error-animation");
      setTimeout(() => {ev.target.classList.remove("error-animation")}, 501)
    }
  }

  return (
    <main id="quiz-view">
      <div className="quiz-container">
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
            <span>Tryb: <span className="important-text">{(isExamMode) ? 'egzamin' : 'nauka'}</span></span>
            <span>Zestaw: <span className="important-text">{questionData.category.toLowerCase()}</span></span>
            <span>Waga: <span className="important-text">{questionData.points}pkt.</span></span>
          </div>
          {
            isExamMode?
              <></>
            :
              <PracticeProgress questionNumber={questionData.number} hardQuestions={questionData._total_hard}></PracticeProgress>
          }
          {
            isExamMode? 
              <ButtonTimerSequence ref={actionbtn} sequence={actionButtonsSequence} index={seqBtnIndex}></ButtonTimerSequence>
            :
              <PrimaryActionButton ref={actionbtn} text="Dalej" onClick={onPracticeNext}></PrimaryActionButton>
          }
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


export function PracticeQuizLoop() {
  const [questionData, setQuestionData] = useState(null);
  const [WSConn, setWSConn] = useState(null);

  useEffect(() => {
    const clientId = localStorage.getItem("CLIENT_ID") ?? "anon";
    const ws = new WebSocket(import.meta.env.VITE_API + "ws/practice/" + clientId);
    
    ws.onmessage = (ev) => {
      console.log(ev)
      const { event, content } = JSON.parse(ev.data);

      if (event == "QUESTION_DATA") {
        setQuestionData(content)
        setIsNextQuestionAnim(false);
      }

      if (event == "SET_CLIENT_ID") {
        localStorage.setItem("CLIENT_ID", content);
      }

      if (event == "ANSWER_VALIDATION") {
        if (content.is_correct) {
          ws.send(JSON.stringify({ "event": "GET_QUESTION", "content": null }))
        } else {
          document.getElementById("possible-answer-" + content.correct_answer).style.backgroundColor = 'green';
          document.getElementById("possible-answer-" + content.given_answer).style.setProperty("background-color", "red", "important");
          setTimeout(() => { ws.send(JSON.stringify({ "event": "GET_QUESTION", "content": null })) }, 3000)
          setIsNextQuestionAnim(true);
        }
      }
    }

    ws.onopen = (ev) => {
      console.log("OPEN")
      ws.send(JSON.stringify({ "event": "GET_QUESTION", "content": null }))
    }

    ws.onerror = (ev) => {
      navigator.reload();
    }


    setWSConn(ws);
  }, [])

  async function checkAnswer(answer) {
    await WSConn.send(JSON.stringify({ "event": "CHECK_ANSWER", "content": answer }))
  }

  const [isNextQuestionAnim, setIsNextQuestionAnim] = useState(false);
  const key = questionData?.index;

  return (
    <>
      {isNextQuestionAnim && <NextQuestionTimeoutAnimation key={'anim-' + key} /> }
      <Quiz key={key} questionData={questionData} isExamMode={false} onContinue={checkAnswer}></Quiz>
    </>
  )
}

