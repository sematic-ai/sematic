import { OpenInNew } from "@mui/icons-material";
import { Button, Tooltip } from "@mui/material";
import { useTextSelection } from "@sematic/common/src/hooks/textSelectionHooks";
import { ValueComponentProps, ViewComponentProps} from "src/typeViz/common";

export function HuggingFaceModelReferenceValueView(props: ViewComponentProps) {
    const { valueSummary } = props;
    const { values } = valueSummary;

    // const bucketSummary = values.bucket.values;

    return <HuggingFaceButton owner="fako" repo="fake" />;
}

export function HuggingFaceDatasetReferenceValueView(props: ViewComponentProps) {
    const { valueSummary } = props;
    const { values } = valueSummary;

    return <HuggingFaceButton owner="fako" repo="fake" />;
}

function HuggingFaceButton(props: { owner?: string, repo: string }) {
    const { owner, repo } = props;

    let href = new URL("https://example.com");

    const elementRef = useTextSelection<HTMLDivElement>();

    return <Tooltip title="View in AWS console">
        <Button
            href={href.href}
            variant="outlined"
            target="blank"
            endIcon={<OpenInNew />}
            draggable={false}
            style={{ userSelect: "text" }}
        >
            <div ref={elementRef} style={{ cursor: "text" }} >🤗{repo}</div>
        </Button>
    </Tooltip>;
}
