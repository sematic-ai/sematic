import styled from "@emotion/styled";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import Box from "@mui/material/Box";
import Skeleton from "@mui/material/Skeleton";
import Tooltip from "@mui/material/Tooltip";
import Typograph from "@mui/material/Typography";
import { useRef } from "react";
import Headline from "src/component/Headline";
import ImportPath from "src/component/ImportPath";
import MoreVertButton from "src/component/MoreVertButton";
import PipelineTitle from "src/component/PipelineTitle";
import Section from "src/component/Section";
import RootRunContext, { useRootRunContext } from "src/context/RootRunContext";
import useBasicMetrics from "src/hooks/metricsHooks";
import PipelineSectionActionMenu from "src/pages/RunDetails/contextMenus/PipelineSectionMenu";
import theme from "src/theme/new";
import { ExtractContextType, RemoveUndefined } from "src/utils/typings";

const TopSection = styled(Section)`
  height: 100px;
  min-height: 100px;
  position: relative;
`;

const BottomSection = styled.section`
  height: 100px;
  border-bottom: 1px solid ${theme.palette.p3border.main};
  display: flex;
  margin: 0 -25px;

  & .MuiBox-root {
    width: 100px;
    min-height: 100px;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
`;

const StyledVertButton = styled(MoreVertButton)`
  position: absolute;
  right: 0;
  top: 12px;
  transform: translate(50%, 0);
`;

const StyledPipelineTitle = styled(PipelineTitle)`
  margin-bottom: ${theme.spacing(2.4)};
  margin-right: ${theme.spacing(2)};
`;

const SkeletonForMetrics = styled(Skeleton)`
    width: 80px;
    margin: 10px ${theme.spacing(2.5)};

    &:first-of-type {
        width: 75px;
        margin-left: ${theme.spacing(5)};
    }
    &:last-of-type {
        width: 75px;
        margin-right: ${theme.spacing(5)};
    }
`;

const StyledErrorOutlineIcon = styled(ErrorOutlineIcon)`
    color: ${theme.palette.error.main};
    width: 18px;
    height: 18px;
`;

function ErrorComponent(props: {
    error: Error
}) {
    const { error } = props;
    return <Tooltip title={error.message}>
        <StyledErrorOutlineIcon />
    </Tooltip>;
}

const PipelineSection = () => {
    const { rootRun } = useRootRunContext() as RemoveUndefined<ExtractContextType<typeof RootRunContext>>;

    const { error, avgRuntime, successRate, totalCount, loading }
        = useBasicMetrics({ runId: rootRun.id, rootFunctionPath: rootRun.function_path });

    const contextMenuAnchor = useRef<HTMLButtonElement>(null);

    return (
        <>
            <TopSection>
                <Headline>Pipeline</Headline>
                <StyledPipelineTitle>{rootRun.name}</StyledPipelineTitle>
                <ImportPath>
                    {rootRun.function_path}
                </ImportPath>
                <StyledVertButton ref={contextMenuAnchor} />
                <PipelineSectionActionMenu anchorEl={contextMenuAnchor.current} />
            </TopSection>
            <BottomSection>
                <>
                    {loading ? <SkeletonForMetrics /> : <Box>
                        <Typograph variant="bigBold">
                            {error ? <ErrorComponent error={error} /> : totalCount}
                        </Typograph>
                        <Typograph variant="body1">runs</Typograph>
                    </Box>}
                    {loading ? <SkeletonForMetrics /> : <Box>
                        <Typograph variant="bigBold">
                            {error ? <ErrorComponent error={error} /> : avgRuntime}
                        </Typograph>
                        <Typograph variant="body1">avg. runtime</Typograph>
                    </Box>}
                    {loading ? <SkeletonForMetrics /> : <Box>
                        <Typograph variant="bigBold">
                            {error ? <ErrorComponent error={error} /> : successRate}
                        </Typograph>
                        <Typograph variant="body1">success</Typograph>
                    </Box>}
                </>
            </BottomSection>
        </>
    );
};

export default PipelineSection;
