import Link from "@mui/material/Link";


interface RunReferenceLinkProps {
    runId: string;
    className?: string;
}

const RunReferenceLink = (props: RunReferenceLinkProps) => {
    const { runId, className } = props;

    return <Link href={`/runs/${runId}`} variant={"small"} type={"code"} className={className}>
            {runId.substring(0, 7)}
        </Link>
}

export default RunReferenceLink;
