import { useEffect, useRef, useState } from "react";
import { AnswersABC, AnswersTN, ButtonTimerSequence, PrimaryActionButton, Modal, SecondaryActionButton } from "./Ui";
import { BadgeQuestionMark, ArrowRight, BookCheck, ChevronLeft, ChevronRight, ArrowLeft, ArrowRightCircle } from 'lucide-react';
import { useHotkeys } from 'react-hotkeys-hook'
import './Quiz.css'
import './Ui.css'


function NextQuestionTimeoutAnimation() {
  const barRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    containerRef.current.style.height = "0px";
    barRef.current.style.width = "0%";
    void barRef.current.offsetWidth;

    containerRef.current.style.height = "6px";
    barRef.current.style.width = "100%";

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
  let hardPercentage = Math.round((hardQuestions / totalQuestions) * 100);
  if (hardQuestions > 0 && hardPercentage < 1) {
    hardPercentage = 1;
  }

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
        <div className="practice-progress-bar-fill" style={{ width: progressPercentage + "%" }}></div>
        <div className="practice-progress-bar-fill-hard" style={{ width: hardPercentage + "%" }}></div>
      </div>
      <span className="practice-progress-hard-count">Błędy: {hardQuestions}</span>
    </div>
  )
}

function ExamProgress({ questionNumber }) {
  const basicQuestions = (questionNumber > 20) ? 20 : questionNumber;
  const basicProgress = (basicQuestions / 20) * 100;
  
  const specQuestions = (questionNumber > 20) ? questionNumber - 20 : 0;
  const specProgress = (specQuestions / 12) * 100;

  return (
    <div className="practice-progress exam-progress">
      <div className="practice-progress">
        <div className="practice-progress-data">
          <span className="important-text">Podstawowe</span>
          <span>
            <span className="important-text">{basicQuestions}</span>/20
          </span>
        </div>
        <div className="practice-progress-bar-container">
          <div className="practice-progress-bar-fill" style={{ width: basicProgress + "%" }}></div>
        </div>
      </div>

      <div className="practice-progress">
        <div className="practice-progress-data">
          <span className="important-text">Specjalistyczne</span>
          <span>
            <span className="important-text">{specQuestions}</span>/12
          </span>
        </div>
        <div className="practice-progress-bar-container">
          <div className="practice-progress-bar-fill" style={{ width: specProgress + "%" }}></div>
        </div>
      </div>
    </div>
  )
}

function getMediaType(filename) {
  return (
    filename.endsWith(".mp4") ? "VIDEO" :
      (
        filename.endsWith(".jpg") ? "IMAGE" : "NOMEDIA"
      )
  )
}

function QuestionMedia({ mediaType, src, ref, id, vidAutoplay }) {
  function onVideoMediaClick(ev) {
    if (vidAutoplay) {
      ev.target.play();
    }
  }
  
  return (
    <>
      {
        mediaType == "VIDEO" &&
        <video id={id} ref={ref} muted autoPlay={vidAutoplay} playsInline src={src} onClick={onVideoMediaClick}></video>
      }

      {
        (mediaType == "IMAGE" || mediaType == "NOMEDIA") &&
        <img id={id} ref={ref} src={src}></img>
      }
    </>
  )
}

export function Quiz({ questionData, isExamMode, onContinue }) {
  if (questionData == null) { return (
    <div className="loader-container">
      <div className="loader"></div> 
    </div>
    )
  }

  const mediaType = getMediaType(questionData.media_name);
  const mediaSrc = (mediaType != "NOMEDIA") ? import.meta.env.VITE_API + "media/" + questionData.media_name : "nomedia.png"

  let actionButtonsSequence;
  if (isExamMode) {
    if (questionData.category == "PODSTAWOWY") {
      actionButtonsSequence = [
        { text: "Start", seconds: 20, kbd: 'Space', onClick: () => { startBasicQuestion() }},
        { text: "Dalej", seconds: 15, kbd: 'Enter', onClick: () => { setSeqBtnPause(false); onContinue(getSelectedAnswer()); actionbtn.current.disabled = true; } },
      ]
    } else {
      actionButtonsSequence = [
        { text: "Dalej", seconds: 50, kbd: 'Enter', onClick: () => { onContinue(getSelectedAnswer()) } },
      ]
    }
  }

  const mediaelement = useRef(null);
  const mediablur = useRef(null);
  const actionbtn = useRef(null);

  function unblurMedia() {
    if (mediablur.current) {
      mediablur.current.style.opacity = 0;
      setTimeout(() => {mediablur.current?.remove()}, 500)
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
    actionbtn.current.disabled = false;

    if (!isExamMode) {
      if (mediaType == "IMAGE" || mediaType == "NOMEDIA") {
        unblurMedia();
        return
      }
      
      if (typeof navigator.getAutoplayPolicy === 'function') { // Firefox
        if (navigator.getAutoplayPolicy("mediaelement") === "disallowed") {
          mediaBlurAsPlayBtn();
        } else {
          mediaelement.current.play();
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
  const [seqBtnPaused, setSeqBtnPause] = useState(false);

  function startBasicQuestion(ev) {
    if (ev?.target.id == "media-blur") {
      if (actionbtn.current.getAttribute("seqnum") == "0") actionbtn.current.click();
    }
    if (mediaType == "VIDEO") {
      setSeqBtnIndex(1)
      setSeqBtnPause(true)

      mediaelement.current.addEventListener("ended", () => { setSeqBtnPause(false) })
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
      actionbtn.current.disabled = true;
    } else {
      ev.target.classList.add("error-animation");
      setTimeout(() => {ev.target.classList.remove("error-animation")}, 501)
    }
  }

  useHotkeys('space', () => startBasicQuestion());
  useHotkeys('enter', () => actionbtn.current.click());

  return (
    <main id="quiz-view" question_index={questionData.index}>
      <div className="quiz-container">
        <div className="quiz-panel media-panel">
          <div className="media-container">
            <QuestionMedia id="display-media" mediaType={mediaType} src={mediaSrc} ref={mediaelement}/>
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
              <ExamProgress questionNumber={questionData.number}></ExamProgress>
            :
              <PracticeProgress questionNumber={questionData.number} hardQuestions={questionData._total_hard}></PracticeProgress>
          }
          {
            isExamMode? 
              <ButtonTimerSequence ref={actionbtn} sequence={actionButtonsSequence} index={seqBtnIndex} paused={seqBtnPaused}></ButtonTimerSequence>
            :
              <PrimaryActionButton ref={actionbtn} id='continue-btn' kbd={"Enter"} text="Dalej" onClick={onPracticeNext}></PrimaryActionButton>
          }
        </div>
        <div className="quiz-panel question-panel">
          <BadgeQuestionMark className="icon"/>
          <span className="question-content">{questionData.question}</span>
        </div>
        <div className="answers-panel">
          <div className="separator"></div>
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



function sessionConnectionHandler(mode, setQuestionData, setIsNextQuestionAnim, setExamResult) {
  if (mode !== "exam" && mode !== "practice") {
    throw new Error(`Invalid connection mode: ${mode} use 'exam' or 'practice'`);
  }
  
  const clientId = localStorage.getItem("CLIENT_ID") ?? "anon";
  const ws = new WebSocket(import.meta.env.VITE_API + "ws/" + mode + "/" + clientId);

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
      if (content == "OK" || content.is_correct) {
        ws.send(JSON.stringify({ "event": "GET_QUESTION", "content": null }))
      } else {
        document.getElementById("possible-answer-" + content.correct_answer).style.backgroundColor = 'green';
        document.getElementById("possible-answer-" + content.given_answer).style.setProperty("background-color", "red", "important");
        setTimeout(() => { ws.send(JSON.stringify({ "event": "GET_QUESTION", "content": null })) }, 3000)
        setIsNextQuestionAnim(true);
      }
    }

    if (event == "EXAM_FINISH") {
      setExamResult(content)
    }
  }

  ws.onopen = (ev) => {
    console.log("OPEN")
    ws.send(JSON.stringify({ "event": "GET_QUESTION", "content": null }))
  }

  return ws;
}

function ExamWrongAnswer({ questionData }) {
  const mediaType = getMediaType(questionData.media_name);
  const mediaSrc = (mediaType != "NOMEDIA") ? import.meta.env.VITE_API + "media/" + questionData.media_name : "nomedia.png"
  const answerShowData = {
    correct: questionData.correct_answer,
    selected: questionData.client_answer
  }

  return (
    <div className="exam-wrong-answer">
      <div className="exam-wrong-media">
        <QuestionMedia mediaType={mediaType} src={mediaSrc} vidAutoplay={true}></QuestionMedia>
      </div>
      <div className="question-panel quiz-panel">
        <BadgeQuestionMark className="icon" />
        <span className="question-content">{questionData.question}</span>
      </div>
      {
        questionData.answers == "TN" ?
          <AnswersTN questionID={'wrong-' + questionData.index} showData={answerShowData}></AnswersTN> :
          <AnswersABC questionID={'wrong-' + questionData.index} showData={answerShowData} answers={questionData.answers}></AnswersABC>
      }
    </div>
  )
}

export function PracticeQuizLoop() {
  const [questionData, setQuestionData] = useState(null);
  const [WSConn, setWSConn] = useState(null);
  const [isNextQuestionAnim, setIsNextQuestionAnim] = useState(false);
  const key = questionData?.index;

  useEffect(() => {
    setWSConn(sessionConnectionHandler("practice", setQuestionData, setIsNextQuestionAnim, () => {}))
  }, [])

  async function checkAnswer(answer) {
    await WSConn.send(JSON.stringify({ "event": "CHECK_ANSWER", "content": answer }))
  }

  return (
    <>
      {isNextQuestionAnim && <NextQuestionTimeoutAnimation key={'anim-' + key} /> }
      <Quiz key={key} questionData={questionData} isExamMode={false} onContinue={checkAnswer}></Quiz>
    </>
  )
}

export function ExamQuizLoop({ onEnd }) {
  const [questionData, setQuestionData] = useState(null);
  const [WSConn, setWSConn] = useState(null);
  const [examResult, setExamResult] = useState(false);
  const [isNextQuestionAnim, setIsNextQuestionAnim] = useState(false);
  const [examResultWrongAnswer, setExamResultWrongAnswer] = useState(0);
  const key = questionData?.index;

  function setupConnection() {
    setWSConn(sessionConnectionHandler("exam", setQuestionData, setIsNextQuestionAnim, setExamResult))
  }

  useEffect(() => {setupConnection()}, [])

  let _has_checked_question = false;
  async function checkAnswer(answer) {
    if (_has_checked_question) return;
    await WSConn.send(JSON.stringify({ "event": "CHECK_ANSWER", "content": answer }))
    _has_checked_question = true
  }

  function endExam() {
    setExamResult(false);
    onEnd();
  }

  function restartExam() {
    setExamResult(false);
    setQuestionData(null);
    setupConnection();
  }

  return (
    <>
      {
        examResult && (
          <Modal title='Egzamin zakończony' icon={BookCheck}>
            <div className="modal-sep"></div>
            <div className="result-status">
              <div className="entry-row sub-panel">
                  <span className="entry-title">Wynik:</span>
                  <span className="entry-value">
                    {
                      examResult.result ? 
                        <span className="success-color">pozytywny</span>
                      :
                        <span className="fail-color">negatywny</span>
                    }
                  </span>
              </div>
  
              <div className="entry-row sub-panel">
                <span className="entry-title">Punkty:</span>
                <span className="entry-value">
                  {examResult.points}<span className="entry-title">/74</span>
                </span>
              </div>

              <div className="wrong-answers-title-row">
                <span className="wrong-answers-title">Błędne odpowiedzi:</span>
                <span className="fail-color">{examResult.incorrect.length}</span>
              </div>
              
              <div className="wrong-answers-controls sub-panel">
                <ChevronLeft className="wrong-answer-control" onClick={() => { setExamResultWrongAnswer((v) => Math.max(v-1, 0))}}/>
                <span>{examResultWrongAnswer + 1}/{examResult.incorrect.length}</span>
                <ChevronRight className="wrong-answer-control" onClick={() => { setExamResultWrongAnswer((v) => Math.min(v + 1, examResult.incorrect.length-1))}}/>
              </div>
              <div className="wrong-answers-container sub-panel">
                {<ExamWrongAnswer questionData={examResult.incorrect[examResultWrongAnswer]}/>}
              </div>  
              
              <div className="modal-sep"></div>
              <div className="row-right">
                <PrimaryActionButton text="Powrót" icon={<ArrowLeft className="icon icon-light"/>} onClick={endExam}></PrimaryActionButton>
                <PrimaryActionButton text="Nowy Egzamin" icon={<BookCheck className="icon icon-light"/>} onClick={restartExam}></PrimaryActionButton>
              </div>
            </div>
          </Modal>
        )
      }

      {isNextQuestionAnim && <NextQuestionTimeoutAnimation key={'anim-' + key} /> }
      <Quiz key={key} questionData={questionData} isExamMode={true} onContinue={checkAnswer}></Quiz>
    </>
  )
}

