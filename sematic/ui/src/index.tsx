import ReactDOM from "react-dom/client";
import App from "./App";
import NewApp, { Shell } from "./NewApp";
import "@fontsource/roboto/300.css";
import "@fontsource/roboto/400.css";
import "@fontsource/roboto/500.css";
import "@fontsource/roboto/700.css";
import "./index.css";
import { Route, BrowserRouter, Routes } from "react-router-dom";
import PipelineIndex from "./pipelines/PipelineIndex";
import PipelineView, { NewPipelineView } from "./pipelines/PipelineView";

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);
root.render(
  <BrowserRouter>
    <Routes>
      <Route path="/new" element={<Shell />}>
        <Route path="pipelines" element={<PipelineIndex />} />
        <Route path="pipelines/:calculatorPath" element={<NewPipelineView />} />
      </Route>
      <Route path="/" element={<App />}>
        <Route path="pipelines/:calculatorPath" element={<PipelineView />} />
      </Route>
    </Routes>
  </BrowserRouter>
);
