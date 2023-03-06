import Typography from "@mui/material/Typography";
import { CommonValueViewProps } from "./common";

export default function FloatValueView(props: CommonValueViewProps) {
  return (
    <Typography display="inline" component="span">
      {Number.parseFloat(props.valueSummary).toFixed(4)}
    </Typography>
  );
}
