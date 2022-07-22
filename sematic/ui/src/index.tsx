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
import { useCallback, useState } from "react";
import {
  CredentialResponse,
  GoogleLogin,
  GoogleOAuthProvider,
} from "@react-oauth/google";

function App() {
  const loginDataFromStorage = localStorage.getItem("loginData");
  const [loginData, setLoginData] = useState(
    loginDataFromStorage ? JSON.parse(loginDataFromStorage) : undefined
  );

  const noAuth = false; //!process.env.AUTHORIZED_DOMAIN;

  const onLogout = useCallback(() => {
    localStorage.removeItem("loginData");
    setLoginData(undefined);
  }, []);

  const onGoogleLoginSuccess = useCallback(
    (credentialResponse: CredentialResponse) => {
      fetch("/login", {
        method: "POST",
        body: JSON.stringify({
          token: credentialResponse.credential,
        }),
        headers: {
          "Content-Type": "application/json",
        },
      });
    },
    []
  );

  return noAuth || loginData ? (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Shell onLogout={onLogout} />}>
          <Route path="" element={<Home />} />
          <Route path="pipelines" element={<PipelineIndex />} />
          <Route path="pipelines/:calculatorPath" element={<PipelineView />} />
        </Route>
      </Routes>
    </BrowserRouter>
  ) : (
    <GoogleLogin
      text="signin_with"
      logo_alignment="center"
      onSuccess={(credentialResponse) => {
        localStorage.setItem("loginData", JSON.stringify(credentialResponse));
        setLoginData(credentialResponse);
      }}
      onError={() => {
        console.log("Login Failed");
      }}
    />
  );
}

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);
root.render(
  <GoogleOAuthProvider clientId="977722105393-257kdkrc5dfbpu0jcsd8etn1k4u4q4ut.apps.googleusercontent.com">
    <App />
  </GoogleOAuthProvider>
);
