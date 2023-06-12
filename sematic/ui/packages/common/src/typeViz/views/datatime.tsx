import { Typography } from "@mui/material";
import Alert from "@mui/material/Alert";
import { format, isValid, parseISO } from "date-fns";
import { ValueComponentProps } from "src/typeViz/common";

export default function DatetimeValueView(props: ValueComponentProps) {
    const { valueSummary } = props;
    const date = parseISO(valueSummary);

    if (!valueSummary || !isValid(date)) {
        return <Alert severity="error" style={{ overflowX: "auto" }}>
            {`Incorrect date value. ${date}`}
        </Alert>;
    }
    return <Typography>{format(date, "LLLL d, yyyy h:mm:ss a xxx")}</Typography>;
}
