import SnackBarContext from "src/context/SnackBarContext"
import { useCallback } from "react";

interface SnackBarProviderProps {
    children: React.ReactNode;
    setSnackMessageOverride?: (message: string) => void;
}

/**
 * This is a temporary solution to show snack messages. It will be replaced with a proper snack bar component.
 */
const SnackBarProvider = ({ children, setSnackMessageOverride }: SnackBarProviderProps) => {
    const setSnackMessage = useCallback((message: string) => {
        (setSnackMessageOverride || console.log)(message);
    }, [setSnackMessageOverride])

    return <SnackBarContext.Provider value={{ setSnackMessage }}>
        {children}
    </SnackBarContext.Provider>
};


export default SnackBarProvider;