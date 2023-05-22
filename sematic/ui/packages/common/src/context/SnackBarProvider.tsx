import SnackBarContext, { SnackMessage } from "src/context/SnackBarContext"
import Snackbar from "@mui/material/Snackbar";
import IconButton from "@mui/material/IconButton";
import CloseIcon from "@mui/icons-material/Close";
import { useMemo, useCallback, useState } from "react";

interface SnackBarProviderProps {
    children: React.ReactNode;
    setSnackMessageOverride?: (message: string) => void;
}

const SnackBarProvider = ({ children, setSnackMessageOverride }: SnackBarProviderProps) => {
    const [snackBarMessage, setSnackMessage] = useState<SnackMessage | undefined>(undefined);

    const onSetSnackBarMessage = useCallback((message: any) => {
        if (setSnackMessageOverride) {
            setSnackMessageOverride(message);
            return;
        }
        setSnackMessage(message);
    }, [setSnackMessageOverride]);

    const snackBarAction = useMemo(() => {
        if (snackBarMessage?.closeable ?? false) {
            return <IconButton
                size="small"
                aria-label="close"
                color="inherit"
                onClick={() => setSnackMessage(undefined)}
            >
                <CloseIcon fontSize="small" />
            </IconButton>
        };
        return undefined
    }, [snackBarMessage]);

    return <SnackBarContext.Provider value={{ setSnackMessage: onSetSnackBarMessage }}>
        {children}
        <Snackbar
            open={snackBarMessage !== undefined}
            message={snackBarMessage?.message}
            anchorOrigin={{ vertical: "top", horizontal: "right" }}
            sx={{ marginTop: "50px" }}
            autoHideDuration={(snackBarMessage?.autoHide ?? true) ? 5000 : undefined}
            onClose={() => {
                setSnackMessage(undefined);
            }}
            action={snackBarAction}
        />
    </SnackBarContext.Provider>
};


export default SnackBarProvider;