import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { RunIndex } from "./runs/RunIndex";
import RunView from "./runs/RunView";
import "@fontsource/roboto/300.css";
import "@fontsource/roboto/400.css";
import "@fontsource/roboto/500.css";
import "@fontsource/roboto/700.css";
import "./index.css";
import { Route, BrowserRouter, Routes } from "react-router-dom";
import PipelineIndex from "./pipelines/PipelineIndex";
import PipelineView from "./pipelines/PipelineView";

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route path="pipelines" element={<PipelineIndex />} />
          <Route path="pipelines/:calculatorPath" element={<PipelineView />} />
          {
            //<Route path="runs/:id" element={<RunView id="abc" />} />
          }
          <Route path="runs" element={<RunIndex />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
