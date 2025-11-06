import { TopPanel } from "./ui/Ui"
import { PracticeQuizLoop, ExamQuizLoop } from "./ui/Quiz"
import { useState } from "react"


export function App() {
  const [isExam, setExam] = useState(false);

  return (
    <>
      <TopPanel startExam={() => {setExam(true)}}/>
      {
        isExam ? <ExamQuizLoop onEnd={() => {setExam(false)}}/> : <PracticeQuizLoop/>
      }
    </>
  )
}

