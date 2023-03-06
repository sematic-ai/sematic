import ReactDOM from "react-dom/client";
import posthog, { Properties } from 'posthog-js';
import "@fontsource/roboto/300.css";
import "@fontsource/roboto/400.css";
import "@fontsource/roboto/500.css";
import "@fontsource/roboto/700.css";
import "./index.css";
import { Route, useNavigate, RouterProvider, createRoutesFromElements, createBrowserRouter, redirect, Outlet } from "react-router-dom";
import PipelineIndex from "./pipelines/PipelineIndex";
import RunView from "./pipelines/PipelineRunView";
import Shell from "./components/Shell";
import Home from "./Home";
import React, { useCallback, useMemo } from "react";
import {
  VersionPayload,
} from "./Payloads";
import { sha1 } from "./utils";
import { SnackBarProvider } from "./components/SnackBarProvider";
import PipelineView from "./pipelines/PipelineView";
import { RunIndex } from "./runs/RunIndex";
import { setupPostHogOptout } from "./postHogManager";
import LoginPage from "./login";
import { ExtractContextType } from "./components/utils/typings";
import AppContext, { UserContext } from "./appContext";
import { useAuthentication, userAtom } from "./hooks/appHooks";
import Loading from "./components/Loading";
import { useAtom } from "jotai";
import { RESET } from "jotai/utils";
import EnvironmentProvider from "./components/EnvironmentProvider";

export const EnvContext = React.createContext<Map<string, string>>(new Map());

function App() {
  const [user, setUser] = useAtom(userAtom);

  const {isAuthenticationEnabled, authProviderDetails, error, loading } = useAuthentication();

  const appContextValue: ExtractContextType<typeof AppContext> = useMemo(() => ({
    authenticationEnabled: isAuthenticationEnabled,
    authProviderDetails
  }), [isAuthenticationEnabled, authProviderDetails]);

  const navigate = useNavigate();

  const signOut = useCallback(() => {
    setUser(RESET);
    navigate("");
  }, [navigate, setUser]);

  const userContextValue = useMemo(
    () => ({
      user,
      signOut,
    }),
    [user, signOut]
  );

  if (error || loading) {
    return <Loading error={error} isLoaded={!loading} />;
  }

  return <AppContext.Provider value={appContextValue}>
      <UserContext.Provider value={userContextValue}>
        <EnvironmentProvider>
          <SnackBarProvider>
            <Outlet />
          </SnackBarProvider>
        </EnvironmentProvider>
      </UserContext.Provider>
    </AppContext.Provider>;
}

const router = createBrowserRouter(
  createRoutesFromElements(
  <Route path="/" element={<App />}>
    <Route path="/login" element={<LoginPage />} />
    <Route element={<Shell />}>
      <Route index element={<Home />} />
      <Route path="pipelines" element={<PipelineIndex />} />
      <Route path="runs" element={<RunIndex />} />
      <Route
        path="pipelines/:pipelinePath/:rootId" 
          loader={({params}) => redirect(`/runs/${params.rootId}`)}
      />
      <Route
        path="pipelines/:pipelinePath" element={<PipelineView />}
      />
      <Route
        path="runs/:rootId" element={<RunView />}
      />
    </Route>
  </Route>
));

function Router() {
  return <RouterProvider router={router} />;
}

(async () => {
  const currentUrl = new URL(window.location.toString());
  const currentHostName = await sha1(currentUrl.hostname);

  const versionResponse: VersionPayload = await (await fetch("/api/v1/meta/versions")).json();
  const serverVersion = versionResponse.server.join('.');

  posthog.init( 
    'phc_nJlFf7MpsrzF5pPaSEQi5GKyTSDjHRcqqL808VLRNXc', { 
      api_host: 'https://app.posthog.com',
      autocapture: false,
      disable_session_recording: true,
      capture_pageview: false,
      capture_pageleave: false,
      persistence: "localStorage",
      property_blacklist: [
        '$referrer', '$referring_domain', '$initial_current_url', '$initial_referrer',
        '$initial_referring_domain', '$pathname', '$initial_pathname'
      ],
      loaded: () => {
        setupPostHogOptout();
        posthog.capture('$pageview');
      },

      sanitize_properties: (properties: Properties, event_name: string) => {
        const currentUrl = new URL(window.location.toString());

        // Use obfuscated host name
        currentUrl.hostname = currentHostName;
        currentUrl.pathname = '[redacted]';
        currentUrl.hash = '';

        if ('$current_url' in properties) {
          properties['$current_url'] = currentUrl.toString();
        }

        if ('$host' in properties) {
          properties['$host'] = currentUrl.host;
        }

        Object.assign(properties, {
          SERVER_VERSION: serverVersion,
          GIT_HASH: process.env.REACT_APP_GIT_HASH,
          NODE_ENV: process.env.NODE_ENV,
          CIRCLECI: process.env.REACT_APP_IS_CIRCLE_CI !== undefined
        })

        return properties;
      }
    }
);

})();

const root = ReactDOM.createRoot(
  document.getElementById("root") as HTMLElement
);
root.render(<Router />);
