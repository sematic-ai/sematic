import { useAtom } from "jotai";
import { EnvContext } from "../index";
import { useEnv, userAtom } from "../hooks/appHooks";
import { ReactNode } from "react";
import Alert from "@mui/material/Alert/Alert";

export default function EnvironmentProvider({ children }: { children: ReactNode }) {
  const [user] = useAtom(userAtom);

  const { value, error } = useEnv(user);

  if (error) {
    return <Alert severity="error" >{error?.message}</Alert>;
  }

  return <EnvContext.Provider value={value}>
    {children}
  </EnvContext.Provider>
}