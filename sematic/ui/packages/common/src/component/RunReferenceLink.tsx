import Link from "@mui/material/Link";
import { TypographyProps } from '@mui/material/Typography';

interface RunReferenceLinkProps {
    runId: string;
    className?: string;
    variant?: TypographyProps['variant'];
}

const RunReferenceLink = (props: RunReferenceLinkProps) => {
    const { runId, className, variant="small" } = props;

    return <Link href={`/runs/${runId}`} variant={variant} type={"code"} className={className}>
            {runId.substring(0, 7)}
        </Link>
}

export default RunReferenceLink;
