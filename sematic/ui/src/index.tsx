import ReactDOM from "react-dom/client";
import "@fontsource/roboto/300.css";
import "@fontsource/roboto/400.css";
import "@fontsource/roboto/500.css";
import "@fontsource/roboto/700.css";
import "./index.css";
import { Route, BrowserRouter, Routes } from "react-router-dom";
import PipelineIndex from "./pipelines/PipelineIndex";
import PipelineView from "./pipelines/PipelineView";
import Shell from "./components/Shell";
import Home from "./Home";
import GoogleLogin from "react-google-login";

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);
root.render(
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<Shell />}>
        <Route path="" element={<Home />} />
        <Route path="pipelines" element={<PipelineIndex />} />
        <Route path="pipelines/:calculatorPath" element={<PipelineView />} />
      </Route>
    </Routes>
  </BrowserRouter>
);
