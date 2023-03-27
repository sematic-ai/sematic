import SnackBarContext from "src/context/SnackBarContext"
import { useCallback } from "react";

interface SnackBarProviderProps {
    children: React.ReactNode;
}

/**
 * This is a temporary solution to show snack messages. It will be replaced with a proper snack bar component.
 */
const SnackBarProvider = ({ children }: SnackBarProviderProps) => {
    const setSnackMessage = useCallback((message: string) => {
        console.log(message);
    }, [])

    return <SnackBarContext.Provider value={{ setSnackMessage }}>
        {children}
    </SnackBarContext.Provider>
};


export default SnackBarProvider;