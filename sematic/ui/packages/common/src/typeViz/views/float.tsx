import Typography from "@mui/material/Typography";
import { ValueComponentProps } from "src/typeViz/common";

export default function FloatValueView(props: ValueComponentProps) {
    return (
        <Typography display="inline" component="span">
            {Number.parseFloat(props.valueSummary).toFixed(4)}
        </Typography>
    );
}
