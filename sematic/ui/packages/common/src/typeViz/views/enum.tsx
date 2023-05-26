import { Chip } from "@mui/material";
import { ValueComponentProps } from "src/typeViz/common";

export default function EnumValueView(props: ValueComponentProps) {
    const { valueSummary } = props;
    return <Chip label={valueSummary} variant="outlined" />;
}
