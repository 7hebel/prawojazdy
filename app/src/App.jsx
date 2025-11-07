import { Modal, TopPanel } from "./ui/Ui"
import { PracticeQuizLoop, ExamQuizLoop } from "./ui/Quiz"
import { AccountView } from "./ui/Account";
import { useState } from "react"
import { User } from "lucide-react";

export function App() {
  const [isExam, setExam] = useState(false);
  const [isAccountView, setIsAccountView] = useState(false);

  return (
    <>
      <TopPanel openAccountView={() => {setIsAccountView(true)}} startExam={() => {setExam(true)}}/>
      {
        isAccountView && <Modal title="Konto" icon={User} close={setIsAccountView}><AccountView closeView={setIsAccountView}/></Modal>
      }
      {
        isExam ? <ExamQuizLoop onEnd={() => {setExam(false)}}/> : <PracticeQuizLoop/>
      }
    </>
  )
}

