import { OpenInNew } from "@mui/icons-material";
import Button from "@mui/material/Button";
import { ValueComponentProps } from "src/typeViz/common";

export default function LinkValueView(props: ValueComponentProps) {
    let { valueSummary } = props;
    let { values } = valueSummary;

    return (
        <Button
            href={values.url}
            variant="contained"
            target="_blank"
            endIcon={<OpenInNew />}
        >
            {values.label}
        </Button>
    );
}
