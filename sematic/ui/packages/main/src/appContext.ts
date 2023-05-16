import React from "react";

export const AppContext = React.createContext<{
    authenticationEnabled: boolean;
    authProviderDetails: {
        google?: {
            GOOGLE_OAUTH_CLIENT_ID: string;
        },
        github?: {
            GITHUB_OAUTH_CLIENT_ID: string;
        }
    };
} | null>(null);

export default AppContext;
  