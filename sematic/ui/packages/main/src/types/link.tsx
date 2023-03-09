import { OpenInNew } from "@mui/icons-material";
import Button from "@mui/material/Button";
import { CommonValueViewProps } from "./common";

export default function LinkValueView(props: CommonValueViewProps) {
    let { valueSummary } = props;
    let { values } = valueSummary;

    return (
        <Button
            href={values.url}
            variant="contained"
            target="blank"
            endIcon={<OpenInNew />}
        >
            {values.label}
        </Button>
    );
}
