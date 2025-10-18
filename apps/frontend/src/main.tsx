import React from "react";
import { createRoot } from "react-dom/client";
import IntegratedApp from "./IntegratedApp";

const root = createRoot(document.getElementById("root")!);
root.render(
  <React.StrictMode>
    <IntegratedApp />
  </React.StrictMode>
);