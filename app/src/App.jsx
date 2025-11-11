import { Modal, TopPanel, ThemeSelector } from "./ui/Ui"
import { PracticeQuizLoop, ExamQuizLoop } from "./ui/Quiz"
import { AccountView } from "./ui/Account";
import { useState } from "react"
import { User, Palette } from "lucide-react";
import { useHotkeys } from 'react-hotkeys-hook'
import { ToastContainer } from 'react-toastify';

export function App() {
  const [isExam, setExam] = useState(false);
  const [isAccountView, setIsAccountView] = useState(false);
  const [isThemeView, setIsThemeView] = useState(false);

  useHotkeys('m', () => {
    const themes = import.meta.env.VITE_THEMES.split(',');
    const currentTheme = localStorage.getItem("theme") ?? "200";
    const currentIndex = themes.indexOf(currentTheme) ?? 0;

    let newIndex = currentIndex + 1;
    if (newIndex > themes.length - 1) { newIndex = 0 }

    const newTheme = themes[newIndex];
    localStorage.setItem("theme", newTheme);
    document.querySelector(':root').style.setProperty('--h-shift', newTheme);
  });


  return (
    <>
      <TopPanel openAccountView={() => { setIsAccountView(true) }} openThemeView={() => { setIsThemeView(true) }}  isExam={isExam} setExam={setExam}/>
      {
        isAccountView && <Modal title="Konto" icon={User} close={setIsAccountView}><AccountView closeView={setIsAccountView}/></Modal>
      }
      {
        isThemeView && <Modal title="Motyw" icon={Palette} close={setIsThemeView}><ThemeSelector closeView={setIsThemeView}/></Modal>
      }
      {
        isExam ? <ExamQuizLoop onEnd={() => {setExam(false)}}/> : <PracticeQuizLoop/>
      }
      <ToastContainer/>
    </>
  )
}

