import { ContentCopy } from "@mui/icons-material";
import { ButtonBase, Tooltip } from "@mui/material";
import { useCallback, useContext } from "react";
import { SnackBarContext } from "./SnackBarProvider";

export function CopyButton(props: {
  text: string;
  message?: string;
  children?: any;
}) {
  const { text, message = "Copied", children } = props;

  const { setSnackMessage } = useContext(SnackBarContext);

  const copy = useCallback(() => {
    navigator.clipboard.writeText(text);
    setSnackMessage({ message: message });
  }, [text, message, setSnackMessage]);
  return (
    <Tooltip title={"Copy " + text}>
      <ButtonBase onClick={copy}>
        {children}
        <ContentCopy fontSize="inherit" sx={{ ml: 1 }} />
      </ButtonBase>
    </Tooltip>
  );
}
