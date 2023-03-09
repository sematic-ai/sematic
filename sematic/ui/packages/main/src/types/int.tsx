import Typography from "@mui/material/Typography";
import { CommonValueViewProps } from "./common";

export default function IntValueView(props: CommonValueViewProps) {
  return (
    <Typography display="inline" component="span">
      {props.valueSummary}
    </Typography>
  );
}
