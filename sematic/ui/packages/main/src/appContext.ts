import React from "react";
import { User } from "./Models";

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

export const UserContext = React.createContext<{
  user: User | null;
  signOut: (() => void) | null;
}>({ user: null, signOut: null });

export default AppContext;
  