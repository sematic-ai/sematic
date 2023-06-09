import Typography from "@mui/material/Typography";
import { ValueComponentProps } from "src/typeViz/common";

export default function IntValueView(props: ValueComponentProps) {
    return (
        <Typography display="inline" component="span">
            {props.valueSummary}
        </Typography>
    );
}
