import Typography from "@mui/material/Typography";
import { CommonValueViewProps } from "./common";

export default function StrValueView(props: CommonValueViewProps) {
    return (
      <Typography component="div">
        <pre>"{props.valueSummary}"</pre>
      </Typography>
    );
}
