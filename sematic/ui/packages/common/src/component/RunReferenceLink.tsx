import styled from "@emotion/styled";
import Link from "@mui/material/Link";
import CopyButton from "src/component/CopyButton";
import theme from "src/theme/new";

const StyledBox = styled.span`
    & svg {
        font-size: ${theme.typography.body1.fontSize}px;
        fill: ${theme.palette.lightGrey.main};
    }
`;

interface RunReferenceLinkProps {
    runId: string;
    className?: string;
}

const RunReferenceLink = (props: RunReferenceLinkProps) => {
    const { runId, className } = props;

    return <StyledBox>
        <Link href={`/runs/${runId}`} variant={"small"} type={"code"} className={className}>
            {runId.substring(0, 7)}
        </Link>
        <CopyButton text={`${window.location.origin}/runs/${runId}`} />
    </StyledBox>
}

export default RunReferenceLink;
