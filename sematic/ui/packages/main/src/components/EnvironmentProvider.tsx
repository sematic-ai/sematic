import Alert from "@mui/material/Alert/Alert";
import EnvContext from "@sematic/common/src/context/envContext";
import { useAtom } from "jotai";
import { ReactNode } from "react";
import { useEnv, userAtom } from "../hooks/appHooks";

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