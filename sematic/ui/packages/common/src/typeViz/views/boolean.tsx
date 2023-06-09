import Chip from "@mui/material/Chip";
import { ValueComponentProps } from "src/typeViz/common";

export function BoolValueViewPresentation({value}: {
    value: boolean;
}) {
    return (
        <Chip
            label={value ? "TRUE" : "FALSE"}
            color={value ? "success" : "error"}
            variant="outlined"
            size="small"
        />
    );
}

export default function BoolValueView(props: ValueComponentProps) {
    let value: boolean = props.valueSummary;
    return <BoolValueViewPresentation value={value} />
}