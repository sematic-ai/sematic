import React from "react";

export const AppContext = React.createContext<{
    authenticatedEnabled: boolean;
    googleAuthClientId: string | undefined;
} | null>(null);

export default AppContext;
  