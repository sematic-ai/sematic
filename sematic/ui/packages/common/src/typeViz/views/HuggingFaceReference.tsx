import { OpenInNew } from "@mui/icons-material";
import { useCallback, useContext, useMemo } from "react";
import { Button, Chip, Tooltip } from "@mui/material";
import { ContentCopy } from "@mui/icons-material";
import SnackBarContext from "@sematic/common/src/context/SnackBarContext";
import { useTextSelection } from "@sematic/common/src/hooks/textSelectionHooks";
import { ViewComponentProps, ValueComponentProps} from "src/typeViz/common";

type Reference = {
    owner: string | null;
    repo: string;
    commit_sha: string | null;
    subset?: string | null | undefined;
}

export function HuggingFaceModelReferenceShortView(props: ValueComponentProps) {
    const { valueSummary } = props;
    const { values } = valueSummary;

    return <HuggingFaceButton
        reference={values}
        objectTypePrefix=""
        short={true}
    />;
}

export function HuggingFaceDatasetReferenceShortView(props: ValueComponentProps) {
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
  
    return <SlugChip reference={values} />;
}

export function HuggingFaceDatasetReferenceValueView(props: ViewComponentProps) {
    const { valueSummary } = props;
    const { values } = valueSummary;

    return <SlugChip reference={values} />;
}

function HuggingFaceButton(props: {
    reference: Reference,
    objectTypePrefix: string,
    short: boolean
}) {
    const { reference, objectTypePrefix, short } = props;
    const { owner, repo, subset, commit_sha } = reference;

    const displayedHref = useMemo(
        () => {
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
            return href;
        }, [owner, repo, subset, commit_sha, objectTypePrefix]
    );

    const displayedSlug = useMemo(
        () => {
            let slug = (owner ? owner + "/" : "") + repo;
            if(subset) {
                slug += ":" + subset;
            }
            if(commit_sha) {
                slug += "@" + commit_sha.substring(0, 7);
            }
  
            if(short) {
                slug = "";
            }
            return slug;
        }, [owner, repo, subset, commit_sha, short]
    );
    const elementRef = useTextSelection<HTMLDivElement>();

    return <Tooltip title="View on Hugging Face">
        <Button
            href={displayedHref.href}
            variant="outlined"
            target="blank"
            endIcon={<OpenInNew />}
            draggable={false}
            style={{ userSelect: "text" }}
        >
            <div ref={elementRef} style={{ cursor: "text" }} >🤗 {displayedSlug}</div>
        </Button>
    </Tooltip>;
}

function SlugChip(props: {
    reference: Reference,
}) {
    const { reference } = props;
    const { owner, repo, subset, commit_sha } = reference;

    const [displayedSlug, fullSlug] = useMemo(
        () => {
            let slug = (owner ? owner + "/" : "") + repo;
            if(subset) {
                slug += ":" + subset;
            }
            let fullSlug = slug;
            if(commit_sha) {
                slug += "@" + commit_sha.substring(0, 7);
                fullSlug += "@" + commit_sha;
            }
            return [slug, fullSlug];
        }, [owner, repo, subset, commit_sha]
    );
    
    const { setSnackMessage } = useContext(SnackBarContext);

    const copy = useCallback(() => {
        setSnackMessage({ message: "Copied " + fullSlug });
        navigator.clipboard.writeText(fullSlug);
    }, [fullSlug, setSnackMessage]);
    
    const contents = useMemo(
        () => {
            return (
                <Tooltip title={"Copy " + fullSlug}>
                    <Chip
                        icon={<ContentCopy />}
                        sx={{ paddingLeft: 2, paddingRight: 2}}
                        onClick={copy}
                        label={"🤗 "+ displayedSlug}
                        variant="outlined"
                    />
                </Tooltip>
            );
        }, [displayedSlug, fullSlug, copy]
    );
    return contents;
}
