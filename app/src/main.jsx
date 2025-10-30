import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import App from "./app";
import UiTest from "./ui/UiTest";
import { PracticeQuizLoop } from "./ui/Quiz";
import './index.css';

const root = document.getElementById("root");



ReactDOM.createRoot(root).render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<App />} />
      <Route path="/ui-test" element={<UiTest />} />
      <Route path="/quiz" element={<PracticeQuizLoop />} />
    </Routes>
  </BrowserRouter>,
);
