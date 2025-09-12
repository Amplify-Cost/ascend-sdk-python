import "./index.css"; // ✅ Tailwind CSS import must be at the top
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";

const root = ReactDOM.createRoot(document.getElementById("root"));

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
// Force rebuild: Sat Sep  6 16:38:17 EDT 2025
