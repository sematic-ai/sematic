import { Chip } from "@mui/material";
import { CommonValueViewProps } from "./common";

export default function EnumValueView(props: CommonValueViewProps) {
    const { valueSummary } = props;
    return <Chip label={valueSummary} variant="outlined" />;
}
