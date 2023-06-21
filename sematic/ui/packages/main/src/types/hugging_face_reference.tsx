import { OpenInNew } from "@mui/icons-material";
import { Button, Tooltip } from "@mui/material";
import { useTextSelection } from "@sematic/common/src/hooks/textSelectionHooks";
import { CommonValueViewProps } from "./common";

export function HuggingFaceModelReferenceValueView(props: CommonValueViewProps) {
    const { valueSummary } = props;
    const { values } = valueSummary;

    const owner = values.owner;
    const repo = values.repo;
    const commitSha = values.commit_sha;

    return <HuggingFaceButton
        owner={owner}
        repo={repo}
        commitSha={commitSha}
        objectTypePrefix=""
    />;
}

export function HuggingFaceDatasetReferenceValueView(props: CommonValueViewProps) {
    const { valueSummary } = props;
    const { values } = valueSummary;
  
    const owner = values.owner;
    const repo = values.repo;
    const subset = values.subset;
    const commitSha = values.commit_sha;

    return <HuggingFaceButton
        owner={owner}
        repo={repo}
        subset={subset}
        commitSha={commitSha}
        objectTypePrefix="/datasets"
    />;
}

function HuggingFaceButton(props: {
    owner?: string,
    repo: string,
    subset?: string,
    commitSha?: string,
    objectTypePrefix: string,
}) {
    const { owner, repo, subset, commitSha, objectTypePrefix } = props;

    const ownerSegment = owner ? "/" + owner : "";
    const repoPath = objectTypePrefix + ownerSegment + "/" + repo;

    // hugging face doesn't allow you to link to a particular
    // commit and subset in the UI at the same time. If there
    // is a specific commit referenced, let that take precedence.
    let path = repoPath;
    if(commitSha) {
        path = repoPath + "/tree/" + commitSha;
    } else if(subset) {
        path = repoPath + "/viewer/" + subset;
    }

    const href = new URL("https://huggingface.co" + path);

    let slug = (owner ? owner + "/" : "") + repo;
    if(subset) {
        slug += ":" + subset;
    }
    if(commitSha) {
        slug += "@" + commitSha.substring(0, 7);
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
