import Link from "@mui/material/Link";
import Typography, { TypographyProps } from "@mui/material/Typography";
import { Link as RouterLink } from "react-router-dom";
import { getRunUrlPattern } from "src/hooks/runHooks";


interface RunReferenceLinkProps {
    runId: string;
    className?: string;
    variant?: TypographyProps["variant"];
}

export const RunReferenceLink = (props: RunReferenceLinkProps) => {
    const { runId, className, variant = "small" } = props;

    return <Link to={getRunUrlPattern(runId)} variant={variant} type={"code"} className={className}
        component={RouterLink}>
        {runId.substring(0, 7)}
    </Link>
}

export const RunReference = (props: RunReferenceLinkProps) => {
    const { runId, className, variant = "code" } = props;

    return <Typography variant={variant} className={className} >
        {runId.substring(0, 7)}
    </Typography>
}
