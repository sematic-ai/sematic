import Chip from "@mui/material/Chip";
import { CommonValueViewProps } from "./common";

export default function BoolValueView(props: CommonValueViewProps) {
    let value: boolean = props.valueSummary;
    return (
      <Chip
        label={value ? "TRUE" : "FALSE"}
        color={value ? "success" : "error"}
        variant="outlined"
        size="small"
      />
    );
}