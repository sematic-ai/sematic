import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { CopyToClipboard } from "react-copy-to-clipboard";

export default function Id(props: { id: string; trimTo?: number }) {
  return (
    <div>
      <CopyToClipboard text={props.id}>
        <Tooltip title={"Click to copy " + props.id} placement="bottom-start">
          <Typography
            fontSize="small"
            color="GrayText"
            sx={{ cursor: "pointer" }}
          >
            <code>
              {props.id.substring(0, props.trimTo || props.id.length)}
            </code>
          </Typography>
        </Tooltip>
      </CopyToClipboard>
    </div>
  );
}
