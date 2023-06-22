import styled from "@emotion/styled";
import Box from "@mui/material/Box";
import Skeleton from "@mui/material/Skeleton";
import parseJSON from "date-fns/parseJSON";
import { useMemo, useRef } from "react";
import { DateTimeLong } from "src/component/DateTime";
import Headline from "src/component/Headline";
import ImportPath from "src/component/ImportPath";
import MoreVertButton from "src/component/MoreVertButton";
import PipelineTitle from "src/component/PipelineTitle";
import { RunReferenceLink } from "src/component/RunReference";
import { getRunStateChipByState } from "src/component/RunStateChips";
import getRunStateText, { DateFormats } from "src/component/RunStateText";
import Section from "src/component/Section";
import TagsList from "src/component/TagsList";
import { useRootRunContext } from "src/context/RootRunContext";
import { useRunDetailsSelectionContext } from "src/context/RunDetailsSelectionContext";
import FunctionSectionActionMenu from "src/pages/RunDetails/contextMenus/FunctionSectionMenu";
import theme from "src/theme/new";

const StyledSection = styled(Section)`
    height: fit-content;
    min-height: 200px;
    position: relative;
    flex-grow: 0;
    flex-shrink: 0;

    &:after {
        content: '';
        position: absolute;
        bottom: 0;
        height: 1px;
        width: calc(100% + ${theme.spacing(10)});
        margin-left: -${theme.spacing(5)};
        background: ${theme.palette.p3border.main};
    }
    
`;

const StyledVertButton = styled(MoreVertButton)`
    position: absolute;
    right: 0;
    top: 12px;
    transform: translate(50%,0);
`;

const BoxContainer = styled(Box)`
    display: flex;
    flex-direction: row;
    height: 35px;
    align-items: center;
    padding-top: ${theme.spacing(1)};
    margin-bottom: ${theme.spacing(4)};

    & .Info {
        margin-left: ${theme.spacing(2)};

        > div {
            display: flex;
            flex-direction: row;
            align-items: center;
            column-gap: ${theme.spacing(2)};
        }
    }
`;

const RunStateContainer = styled(Box)`
    flex-grow: 0;
    width: 25px;
`

const ImportPathContainer = styled(Box)`
    margin-bottom: ${theme.spacing(4)};
`

const TagsContainer = styled(Box)`
  display: flex;
  align-items: center;
  justify-content: flex-start;
  & .tags-list-wrapper {
    width: auto;
    flex-grow: 0;
  }
`;

const StyledRunReferenceLink = styled(RunReferenceLink)`
    font-size: ${theme.typography.fontSize}px ;
`;

const SmallPlaceholderSkeleton = styled(Skeleton)`
    width: 25px;
`;

const MediumPlaceholderSkeleton = styled(Skeleton)`
    width: 100px;
`;

const LongPlaceholderSkeleton = styled(Skeleton)`
    width: 300px;
`;

const FunctionName = PipelineTitle

const FunctionSection = () => {
    const { isGraphLoading } = useRootRunContext();
    const { selectedRun } = useRunDetailsSelectionContext();

    const statusText = useMemo(() => {
        if (!selectedRun) {
            return null;
        }

        const runDuration = getRunStateText(selectedRun.future_state, {
            createdAt: selectedRun.created_at as unknown as string,
            failedAt: selectedRun.failed_at as unknown as string,
            resolvedAt: selectedRun.resolved_at as unknown as string
        }, DateFormats.LONG);

        if (!(selectedRun.resolved_at || selectedRun.failed_at|| selectedRun.ended_at)){
            return runDuration;
        }

        const completeAt = DateTimeLong(parseJSON((selectedRun.resolved_at || selectedRun.failed_at
            || selectedRun.ended_at) as unknown as string));

        return `${runDuration} on ${completeAt}`;
    }, [selectedRun]);

    const contextMenuAnchor = useRef<HTMLButtonElement>(null);

    return <StyledSection>
        <Headline>Function Run</Headline>
        <BoxContainer>
            <RunStateContainer>
                {isGraphLoading ? <SmallPlaceholderSkeleton /> : getRunStateChipByState(selectedRun!.future_state)}
            </RunStateContainer>
            <div className='Info'>
                <FunctionName>
                    {isGraphLoading ? <MediumPlaceholderSkeleton /> : selectedRun!.name}
                </FunctionName>
                <div>
                    {isGraphLoading ? <MediumPlaceholderSkeleton /> : <StyledRunReferenceLink runId={selectedRun!.id} />}
                    {isGraphLoading ? <LongPlaceholderSkeleton /> : statusText}
                </div>
            </div>
        </BoxContainer>
        <ImportPathContainer>
            {isGraphLoading ? <LongPlaceholderSkeleton />
                : <ImportPath>{selectedRun?.function_path}</ImportPath>}
        </ImportPathContainer>
        <StyledVertButton ref={contextMenuAnchor} />
        <FunctionSectionActionMenu anchorEl={contextMenuAnchor.current} />
        {isGraphLoading ? <MediumPlaceholderSkeleton />
            : <TagsContainer>
                <div className={"tags-list-wrapper"} key={selectedRun?.id}><TagsList tags={selectedRun?.tags || []} /></div>
                {/** Adding tag is not currently supported will re-enable later */}
                {/* <Button variant={"text"} size={"small"} style={
                    {...(isEmpty(selectedRun?.tags) ? {marginLeft: "-8px"} : {})}
                }>add tags</Button> */}
            </TagsContainer>}
    </StyledSection>;
}

export default FunctionSection;
