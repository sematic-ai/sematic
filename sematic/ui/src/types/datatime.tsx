import { Typography } from "@mui/material";
import Alert from "@mui/material/Alert";
import { CommonValueViewProps } from "./common";
import { format, isValid, parseISO } from "date-fns";

export default function DatetimeValueView(props: CommonValueViewProps) {
    const { valueSummary } = props;
    const date = parseISO(valueSummary);
  
    if (!valueSummary || !isValid(date)) {
      return <Alert severity="error">Incorrect date value.</Alert>;
    }
    return <Typography>{format(date, "LLLL d, yyyy h:mm:ss a xxx")}</Typography>;
  }