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
import {
  AuthenticatePayload,
  EnvPayload,
  GoogleLoginPayload,
} from "./Payloads";
import { User } from "./Models";
import { Alert, Paper } from "@mui/material";
import logo from "./Fox.png";
import { fetchJSON } from "./utils";
import { SnackBarProvider } from "./components/SnackBarProvider";

export const UserContext = React.createContext<{
  user: User | null;
  signOut: (() => void) | null;
}>({ user: null, signOut: null });

export const EnvContext = React.createContext<Map<string, string>>(new Map());

function App() {
  const userFromStorage = localStorage.getItem("user");
  const [user, setUser] = useState<User | null>(
    userFromStorage ? JSON.parse(userFromStorage) : null
  );
  const [authenticate, setAuthenticate] = useState<
    AuthenticatePayload | undefined
  >(undefined);
  const [env, setEnv] = useState<Map<string, string>>(new Map());
  const [error, setError] = useState<Error | undefined>(undefined);

  useEffect(() => {
    fetchJSON({
      url: "/authenticate",
      callback: (payload: AuthenticatePayload) => {
        setAuthenticate(payload);
      },
      setError: setError,
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

  useEffect(() => {
    if (!user) {
      setEnv(new Map());
    }
    fetchJSON({
      url: "/api/v1/meta/env",
      callback: (payload: EnvPayload) => {
        setEnv(new Map(Object.entries(payload.env)));
      },
      apiKey: user?.api_key,
    });
  }, [user]);

  const envContextValue = useMemo(() => env, [env]);

  const onGoogleLoginSuccess = useCallback(
    (credentialResponse: CredentialResponse) => {
      fetchJSON({
        url: "/login/google",
        method: "POST",
        body: {
          token: credentialResponse.credential,
        },
        callback: (payload: GoogleLoginPayload) => {
          setError(undefined);
          localStorage.setItem("user", JSON.stringify(payload.user));
          setUser(payload.user);
        },
        setError: setError,
      });
    },
    []
  );

  return authenticate?.authenticate === false || user ? (
    <UserContext.Provider value={userContextValue}>
      <EnvContext.Provider value={envContextValue}>
        <SnackBarProvider>
          <Routes>
            <Route path="/" element={<Shell />}>
              <Route path="" element={<Home />} />
              <Route path="pipelines" element={<PipelineIndex />} />
              <Route
                path="pipelines/:calculatorPath/:rootId"
                element={<PipelineView />}
              />
              <Route
                path="pipelines/:calculatorPath"
                element={<PipelineView />}
              />
            </Route>
          </Routes>
        </SnackBarProvider>
      </EnvContext.Provider>
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

      {error ? <Alert severity="error">{error.message}</Alert> : <></>}

      {!error &&
      authenticate &&
      authenticate.authenticate === true &&
      authenticate.providers.GOOGLE_OAUTH_CLIENT_ID !== undefined ? (
        <GoogleOAuthProvider
          clientId={authenticate.providers.GOOGLE_OAUTH_CLIENT_ID}
        >
          <GoogleLogin
            text="signin_with"
            logo_alignment="center"
            onSuccess={onGoogleLoginSuccess}
            onError={() => {
              setError(Error("Unauthorized user"));
            }}
          />
        </GoogleOAuthProvider>
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
  <BrowserRouter>
    <App />
  </BrowserRouter>
);
