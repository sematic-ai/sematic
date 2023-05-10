import { Button, IconButton, Snackbar } from "@mui/material";
import { Alert } from "@mui/material";
import { useMemo, useState } from "react";
import SnackBarContext from "@sematic/common/src/context/SnackBarContext";
import CloseIcon from "@mui/icons-material/Close";

export enum MessageKind {
  Info,
  Error,
}

export type SnackMessage = {
  message: string;
  actionName?: string;
  onClick?: () => void;
  closable?: boolean;
  autoHide?: boolean;
  kind?: MessageKind;
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

  const kind = useMemo(() => (!!snackMessage && snackMessage.kind) || MessageKind.Info, [snackMessage]);

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

  const content = useMemo( 
    () => {
      const severity = kind === MessageKind.Info ? "info" : "error";
      return (
        <Alert
          severity={severity}
          onClick={() => {
            if(closable) {
              setSnackMessage(undefined);
            }
          }}
        >
          {snackMessage?.message}
          {snackBarAction}
        </Alert>
      );
    }, [snackMessage, kind, snackBarAction, closable]
  );

  return (
    <SnackBarContext.Provider value={{ setSnackMessage }}>
      {children}
      <Snackbar
        open={snackMessage !== undefined}
        anchorOrigin={{ vertical: "top", horizontal: "right" }}
        sx={{ marginTop: "50px" }}
        autoHideDuration={autoHide ? 5000 : undefined}
        onClose={() => {
          setSnackMessage(undefined);
        }}
      >
        {content}
      </Snackbar>
    </SnackBarContext.Provider>
  );
}
