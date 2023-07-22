import Link from "@mui/material/Link";
import Typography, { TypographyProps } from "@mui/material/Typography";
import { useCallback } from "react";
import { useRunNavigation } from "src/hooks/runHooks";


interface RunReferenceLinkProps {
    runId: string;
    className?: string;
    variant?: TypographyProps["variant"];
}

export const RunReferenceLink = (props: RunReferenceLinkProps) => {
    const { runId, className, variant = "small" } = props;

    const navigate = useRunNavigation();

    const onClick = useCallback(() => {
        navigate(runId);
    }, [navigate, runId]);

    return <Link onClick={onClick} variant={variant} type={"code"} className={className}>
        {runId.substring(0, 7)}
    </Link>
}

export const RunReference = (props: RunReferenceLinkProps) => {
    const { runId, className, variant = "code" } = props;

    return <Typography variant={variant} className={className} >
        {runId.substring(0, 7)}
    </Typography>
}
