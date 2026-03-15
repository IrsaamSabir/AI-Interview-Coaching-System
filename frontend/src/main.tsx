import { createRoot } from "react-dom/client";
import App from "./App";   // make sure App.tsx is in the same folder
import "./index.css";

createRoot(document.getElementById("root")!).render(<App />);
