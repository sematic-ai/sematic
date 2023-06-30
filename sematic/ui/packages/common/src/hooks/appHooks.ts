import { useContext } from "react";
import AppContext from "src/context/appContext";

export function useAppContext() {
    const contextValue = useContext(AppContext);

    if (!contextValue) {
        throw new Error("useAppContext() should be called under a provider.")
    }

    return contextValue;
}
