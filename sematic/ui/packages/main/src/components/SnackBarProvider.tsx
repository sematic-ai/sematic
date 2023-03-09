import { Button, IconButton, Snackbar } from "@mui/material";
import { createContext, useMemo, useState } from "react";
import CloseIcon from "@mui/icons-material/Close";

export const SnackBarContext = createContext<{
  setSnackMessage?: any;
}>({});

export type SnackMessage = {
  message: string;
  actionName?: string;
  onClick?: () => void;
  closable?: boolean;
  autoHide?: boolean;
};

export function SnackBarProvider(props: { children: any }) {
  const [snackMessage, setSnackMessage] = useState<SnackMessage | undefined>(
    undefined
  );

  const { children } = props;

  const closable = useMemo(
    () =>
      snackMessage
        ? snackMessage.closable === undefined
          ? false
          : snackMessage.closable
        : undefined,
    [snackMessage]
  );

  const autoHide = useMemo(
    () =>
      snackMessage
        ? snackMessage.autoHide === undefined
          ? true
          : snackMessage.autoHide
        : undefined,
    [snackMessage]
  );

  const snackBarAction = useMemo(
    () => (
      <>
        <Button
          size="small"
          onClick={() => {
            snackMessage && snackMessage.onClick && snackMessage.onClick();
            setSnackMessage(undefined);
          }}
        >
          {snackMessage?.actionName}
        </Button>
        {closable ? (
          <IconButton
            size="small"
            aria-label="close"
            color="inherit"
            onClick={() => setSnackMessage(undefined)}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        ) : (
          <></>
        )}
      </>
    ),
    [snackMessage, closable]
  );

  return (
    <SnackBarContext.Provider value={{ setSnackMessage }}>
      {children}
      <Snackbar
        open={snackMessage !== undefined}
        anchorOrigin={{ vertical: "top", horizontal: "right" }}
        message={snackMessage?.message}
        sx={{ marginTop: "50px" }}
        autoHideDuration={autoHide ? 5000 : undefined}
        onClose={() => {
          setSnackMessage(undefined);
        }}
        action={snackMessage?.actionName ? snackBarAction : <></>}
      />
    </SnackBarContext.Provider>
  );
}
