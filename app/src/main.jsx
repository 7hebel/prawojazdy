import ReactDOM from "react-dom/client";
import { App } from "./App";
import './index.css';

const root = document.getElementById("root");
document.querySelector(':root').style.setProperty('--h-shift', localStorage.getItem('theme') ?? 200)

ReactDOM.createRoot(root).render(<App/>);
