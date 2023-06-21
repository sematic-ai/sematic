import { OpenInNew } from "@mui/icons-material";
import { Button, Tooltip } from "@mui/material";
import { useTextSelection } from "@sematic/common/src/hooks/textSelectionHooks";
import { CommonValueViewProps } from "./common";

type Reference = {
    owner: string | null;
    repo: string;
    commit_sha: string | null;
    subset?: string | null | undefined;
}

export function HuggingFaceModelReferenceValueView(props: CommonValueViewProps) {
    const { valueSummary } = props;
    const { values } = valueSummary;

    return <HuggingFaceButton
        reference={values}
        objectTypePrefix=""
    />;
}

export function HuggingFaceDatasetReferenceValueView(props: CommonValueViewProps) {
    const { valueSummary } = props;
    const { values } = valueSummary;
  
    return <HuggingFaceButton
        reference={values}
        objectTypePrefix="/datasets"
    />;
}

function HuggingFaceButton(props: {
    reference: Reference,
    commitSha?: string,
    objectTypePrefix: string,
}) {

    const { reference, objectTypePrefix } = props;
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
