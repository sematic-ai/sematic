import "@fontsource/roboto/300.css";
import "@fontsource/roboto/400.css";
import "@fontsource/roboto/500.css";
import "@fontsource/roboto/700.css";
import UserContext from "@sematic/common/src/context/UserContext";
import AppContext from "@sematic/common/src/context/appContext";
import NewShell, { HeaderSelectionKey } from "@sematic/common/src/layout/Shell";
import GettingStarted from "@sematic/common/src/pages/GettingStarted";
import PipelineList from "@sematic/common/src/pages/PipelineList";
import PipelineRuns from "@sematic/common/src/pages/PipelineRuns";
import NewRunDetails from "@sematic/common/src/pages/RunDetails";
import NewRunSearch from "@sematic/common/src/pages/RunSearch";
import { getFeatureFlagValue } from "@sematic/common/src/utils/FeatureFlagManager";
import { ExtractContextType } from "@sematic/common/src/utils/typings";
import { useAtom } from "jotai";
import { RESET } from "jotai/utils";
import posthog, { Properties } from "posthog-js";
import React, { useCallback, useMemo } from "react";
import ReactDOM from "react-dom/client";
import { Outlet, Route, RouterProvider, createBrowserRouter, createRoutesFromElements, redirect, useNavigate } from "react-router-dom";
import "reactflow/dist/style.css";
import Helper from "src/components/tests/tеst_normal";
import Home from "./Home";
import {
    VersionPayload,
} from "./Payloads";
import EnvironmentProvider from "./components/EnvironmentProvider";
import Health from "./components/Health";
import Loading from "./components/Loading";
import Shell from "./components/Shell";
import { SnackBarProvider } from "./components/SnackBarProvider";
import { useAuthentication, userAtom } from "./hooks/appHooks";
import "./index.css";
import LoginPage from "./login";
import PipelineIndex from "./pipelines/PipelineIndex";
import RunView from "./pipelines/PipelineRunView";
import PipelineView from "./pipelines/PipelineView";
import { setupPostHogOptout } from "./postHogManager";
import { RunIndex } from "./runs/RunIndex";
import { sha1 } from "./utils";

export const EnvContext = React.createContext<Map<string, string>>(new Map());

function App() {
    const [user, setUser] = useAtom(userAtom);

    const { isAuthenticationEnabled, authProviderDetails, error, loading } = useAuthentication();

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
                    <Helper />
                    <Health />
                    <Outlet />
                </SnackBarProvider>
            </EnvironmentProvider>
        </UserContext.Provider>
    </AppContext.Provider>;
}

const isNewUIEnabled = getFeatureFlagValue("newui");

const NewRoutesOverrides = isNewUIEnabled ? (<>
    <Route path="runs" element={<NewShell />} >
        <Route index element={<NewRunSearch />} handle={{[HeaderSelectionKey]: "runs"}} />
    </Route>
    <Route path="pipelines" element={<NewShell />} >
        <Route index element={<PipelineList />} handle={{[HeaderSelectionKey]: "pipelines"}} />
    </Route>
    <Route path="pipeline/:functionPath" element={<NewShell />} >
        <Route index element={<PipelineRuns />} />
    </Route>
    <Route path="runs/:rootId" element={<NewShell />} >
        <Route index element={<NewRunDetails />} />
    </Route>
    <Route path="/" element={<NewShell />} >
        <Route index element={<GettingStarted />} handle={{[HeaderSelectionKey]: "gettingstarted"}} />
    </Route>
</>) : null;

const router = createBrowserRouter(
    createRoutesFromElements(
        <Route path="/" element={<App />}>
            <Route path="/login" element={<LoginPage />} />
            {NewRoutesOverrides}
            <Route element={<Shell />}>
                <Route index element={<Home />} />
                <Route path="pipelines" element={<PipelineIndex />} />
                <Route path="runs" element={<RunIndex />} />
                <Route
                    path="pipelines/:pipelinePath/:rootId"
                    loader={({ params }) => redirect(`/runs/${params.rootId}`)}
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
    const serverVersion = versionResponse.server.join(".");

    posthog.init(
        "phc_nJlFf7MpsrzF5pPaSEQi5GKyTSDjHRcqqL808VLRNXc", {
            api_host: "https://app.posthog.com",
            autocapture: false,
            disable_session_recording: true,
            capture_pageview: false,
            capture_pageleave: false,
            persistence: "localStorage",
            property_blacklist: [
                "$referrer", "$referring_domain", "$initial_current_url", "$initial_referrer",
                "$initial_referring_domain", "$pathname", "$initial_pathname"
            ],
            loaded: () => {
                setupPostHogOptout();
                posthog.capture("$pageview");
            },

            sanitize_properties: (properties: Properties, event_name: string) => {
                const currentUrl = new URL(window.location.toString());

                // Use obfuscated host name
                currentUrl.hostname = currentHostName;
                currentUrl.pathname = "[redacted]";
                currentUrl.hash = "";

                if ("$current_url" in properties) {
                    properties["$current_url"] = currentUrl.toString();
                }

                if ("$host" in properties) {
                    properties["$host"] = currentUrl.host;
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
