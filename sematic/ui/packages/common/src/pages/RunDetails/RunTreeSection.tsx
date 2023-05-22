import styled from "@emotion/styled";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Headline from "src/component/Headline";
import RunTree, { RunTreeSkeleton } from "src/component/RunTree";
import Section from "src/component/Section";
import { useRootRunContext } from "src/context/RootRunContext";
import { useRunDetailsSelectionContext } from "src/context/RunDetailsSelectionContext";
import { useRunsTree } from "src/hooks/graphHooks";
import theme from "src/theme/new";

const StyledSection = styled(Section)`
    display: flex;
    flex-direction: column;
`

const ScrollableStyledSection = styled(StyledSection)`
    margin-top: 0;
    margin-bottom: ${theme.spacing(3)};
    overflow-y: auto;
    overflow-x: hidden;
    direction: rtl;
    margin-left: -25px;
    margin-right: -25px;
    scrollbar-gutter: stable;
    flex-shrink: 1!important;

    &::-webkit-scrollbar {
      display: block;
      width: 16px;
    }
    
    &::-webkit-scrollbar-button {
      display: none;
    }
    
    &::-webkit-scrollbar-track {
      background-color: #00000000;
    }
    
    &::-webkit-scrollbar-track-piece {
      background-color: #00000000;
    }
    
    &::-webkit-scrollbar-thumb {
      background-color: #00000040;
      border: 1px solid #ffffff40;
      border-radius: 24px;
    }

    &::-webkit-scrollbar-thumb:hover {
        background-color: #00000060;
    }

`;

const StyledTypography = styled(Typography)`
    height: ${theme.spacing(6)};
    align-items: center;
    display: flex;
`;
const RunTreeContainer = styled(Box)`
    direction: ltr;
    margin-left: ${theme.spacing(2)};
`;

const RunTreeSection = () => {
    const { graph, isGraphLoading } = useRootRunContext();
    const { selectedRun, setSelectedRunId } = useRunDetailsSelectionContext();

    const runTreeNode = useRunsTree(graph);

    return <>
        <StyledSection>
            <Headline>Graph</Headline>
            <StyledTypography >Execution Graph</StyledTypography>
        </StyledSection>
        <ScrollableStyledSection>
            <RunTreeContainer>
                {isGraphLoading ?
                    <RunTreeSkeleton /> :
                    <RunTree runTreeNodes={runTreeNode?.children || []} selectedRunId={selectedRun?.id}
                        onSelect={setSelectedRunId} />
                }
            </RunTreeContainer>
        </ScrollableStyledSection>
    </>;
}

export default RunTreeSection;
