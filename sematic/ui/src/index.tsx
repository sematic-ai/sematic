import ReactDOM from "react-dom/client";
import "@fontsource/roboto/300.css";
import "@fontsource/roboto/400.css";
import "@fontsource/roboto/500.css";
import "@fontsource/roboto/700.css";
import "./index.css";
import { Route, BrowserRouter, Routes, useNavigate } from "react-router-dom";
import PipelineIndex from "./pipelines/PipelineIndex";
import PipelineView from "./pipelines/PipelineView";
import Shell from "./components/Shell";
import Loading from "./components/Loading";
import Home from "./Home";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  CredentialResponse,
  GoogleLogin,
  GoogleOAuthProvider,
} from "@react-oauth/google";
import { GoogleLoginPayload } from "./Payloads";
import { User } from "./Models";
import { Paper } from "@mui/material";
import logo from "./Fox.png";
import { fetchJSON } from "./utils";

export const UserContext = React.createContext<{
  user: User | null;
  signOut: (() => void) | null;
}>({ user: null, signOut: null });

function App() {
  const userFromStorage = localStorage.getItem("user");
  const [user, setUser] = useState<User | null>(
    userFromStorage ? JSON.parse(userFromStorage) : null
  );
  const [authenticate, setAuthenticate] = useState<boolean | undefined>(
    undefined
  );

  useEffect(() => {
    fetchJSON("/authenticate", (payload: { authenticate: boolean }) => {
      setAuthenticate(payload.authenticate);
    });
  }, []);

  const navigate = useNavigate();

  const signOut = useCallback(() => {
    localStorage.removeItem("user");
    setUser(null);
    navigate("");
  }, []);

  const userContextValue = useMemo(
    () => ({
      user,
      signOut,
    }),
    [user, signOut]
  );

  const onGoogleLoginSuccess = useCallback(
    (credentialResponse: CredentialResponse) => {
      fetch("/login/google", {
        method: "POST",
        body: JSON.stringify({
          token: credentialResponse.credential,
        }),
        headers: {
          "Content-Type": "application/json",
        },
      })
        .then((response) => response.json())
        .then((payload: GoogleLoginPayload) => {
          localStorage.setItem("user", JSON.stringify(payload));
          setUser(payload);
        });
    },
    []
  );

  return authenticate === false || user ? (
    <UserContext.Provider value={userContextValue}>
      <Routes>
        <Route path="/" element={<Shell />}>
          <Route path="" element={<Home />} />
          <Route path="pipelines" element={<PipelineIndex />} />
          <Route path="pipelines/:calculatorPath" element={<PipelineView />} />
        </Route>
      </Routes>
    </UserContext.Provider>
  ) : (
    <Paper
      sx={{
        width: 200,
        p: 5,
        textAlign: "center",
        top: "50%",
        left: "50%",
        position: "absolute",
        transform: "translateY(-50%) translateX(-50%)",
      }}
      variant="outlined"
    >
      <img
        src={logo}
        width="50px"
        alt="Sematic logo"
        style={{ marginBottom: "30px" }}
      />
      {authenticate === undefined ? <Loading isLoaded={false} /> : <></>}
      {authenticate === true ? (
        <GoogleLogin
          text="signin_with"
          logo_alignment="center"
          onSuccess={onGoogleLoginSuccess}
          onError={() => {
            console.log("Login Failed");
          }}
        />
      ) : (
        <></>
      )}
    </Paper>
  );
}

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);
root.render(
  <GoogleOAuthProvider clientId="977722105393-257kdkrc5dfbpu0jcsd8etn1k4u4q4ut.apps.googleusercontent.com">
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </GoogleOAuthProvider>
);
