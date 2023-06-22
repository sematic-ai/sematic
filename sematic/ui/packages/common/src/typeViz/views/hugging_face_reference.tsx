import { OpenInNew } from "@mui/icons-material";
import { Button, Tooltip } from "@mui/material";
import { useTextSelection } from "@sematic/common/src/hooks/textSelectionHooks";
import { ViewComponentProps} from "src/typeViz/common";

type Reference = {
    owner: string | null;
    repo: string;
    commit_sha: string | null;
    subset?: string | null | undefined;
}

export function HuggingFaceModelReferenceShortView(props: ViewComponentProps) {
    const { valueSummary } = props;
    const { values } = valueSummary;

    return <HuggingFaceButton
        reference={values}
        objectTypePrefix=""
        short={true}
    />;
}

export function HuggingFaceDatasetReferenceShortView(props: ViewComponentProps) {
    const { valueSummary } = props;
    const { values } = valueSummary;

    return <HuggingFaceButton
        reference={values}
        objectTypePrefix="/datasets"
        short={true}
    />;
}

export function HuggingFaceModelReferenceValueView(props: ViewComponentProps) {
    const { valueSummary } = props;
    const { values } = valueSummary;
  
    return <HuggingFaceButton
        reference={values}
        objectTypePrefix=""
        short={false}
    />;

}

export function HuggingFaceDatasetReferenceValueView(props: ViewComponentProps) {
    const { valueSummary } = props;
    const { values } = valueSummary;

    return <HuggingFaceButton
        reference={values}
        objectTypePrefix="/datasets"
        short={false}
    />;
}

function HuggingFaceButton(props: {
    reference: Reference,
    objectTypePrefix: string,
    short: boolean
}) {
    const { reference, objectTypePrefix, short } = props;
    const { owner, repo, subset, commit_sha } = reference;

    const ownerSegment = owner ? "/" + owner : "";
    const repoPath = objectTypePrefix + ownerSegment + "/" + repo;

    // hugging face doesn't allow you to link to a particular
    // commit and subset in the UI at the same time. If there
    // is a specific commit referenced, let that take precedence.
    let path = repoPath;
    if(commit_sha) {
        path = repoPath + "/tree/" + commit_sha;
    } else if(subset) {
        path = repoPath + "/viewer/" + subset;
    }

    const href = new URL("https://huggingface.co" + path);

    let slug = (owner ? owner + "/" : "") + repo;
    if(subset) {
        slug += ":" + subset;
    }
    if(commit_sha) {
        slug += "@" + commit_sha.substring(0, 7);
    }
  
    const elementRef = useTextSelection<HTMLDivElement>();
    if(short) {
        slug = "";
    }

    return <Tooltip title="View on Hugging Face">
        <Button
            href={href.href}
            variant="outlined"
            target="blank"
            endIcon={<OpenInNew />}
            draggable={false}
            style={{ userSelect: "text" }}
        >
            <div ref={elementRef} style={{ cursor: "text" }} >🤗 {slug}</div>
        </Button>
    </Tooltip>;
}
