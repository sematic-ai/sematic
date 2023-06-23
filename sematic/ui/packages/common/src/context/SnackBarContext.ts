import { createContext } from "react";
import noop from "lodash/noop";


export type SnackMessage = {
    message: string;
    closeable?: boolean;
    autoHide?: boolean;
    actionName?: string;
    onClick?: () => void;
}

const SnackBarContext = createContext<{
    setSnackMessage: <T extends SnackMessage>(message: T) => void;
}>({ setSnackMessage: noop });

export default SnackBarContext;
