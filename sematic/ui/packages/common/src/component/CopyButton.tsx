import { ContentCopy } from "@mui/icons-material";
import { ButtonBase, Tooltip } from "@mui/material";
import { useCallback, useContext } from "react";
import SnackBarContext from "src/context/SnackBarContext";

export function CopyButton(props: {
  text: string;
  message?: string;
  children?: any;
  color?: string;
}) {
  const { text, message = "Copied", children, color = undefined } = props;

  const { setSnackMessage } = useContext(SnackBarContext);

  const copy = useCallback(() => {
    navigator.clipboard.writeText(text);
    setSnackMessage({ message: message });
  }, [text, message, setSnackMessage]);
  return (
    <Tooltip title={"Copy " + text}>
      <ButtonBase onClick={copy}>
        {children}
        <ContentCopy htmlColor={color} fontSize="inherit" sx={{ ml: 1 }} />
      </ButtonBase>
    </Tooltip>
  );
}

export default CopyButton;