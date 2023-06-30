import styled from "@emotion/styled";
import { Button } from "@mui/material";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import { useTheme } from "@mui/material/styles";
import { useLogStream } from "@sematic/common/src/hooks/logHooks";
import { useScrollTracker } from "@sematic/common/src/hooks/scrollingHooks";
import { useCallback, useEffect, useState } from "react";
import theme from "src/theme/new";

const Container = styled(Box)`
    display: flex;
    flex-direction: column;
`;

const ScrollableContainer = styled(Box)`
    overflow-y: auto;
    flex-grow: 1;
    flex-shrink: 0;
`;

const StyledButton = styled(Button)`
    width: 100%;
    flex-shrink: 0;
    flex-grow: 0;
    background-color: ${theme.palette.background.paper};

    &:hover {
        background-color: ${theme.palette.grey[50]}
    }
`;

const JumpToBeginningButton = styled(StyledButton)`
    position: sticky;
    top: 0;
`;

enum Buttons {
    JumpToBeginning,
    JumpToEnd,
    LoadPrevious,
    LoadNext
}

const loadingText = "loading...";
interface BidirectionalLogViewProps {
    logSource: string;
    filterString: string;
    setIsLoading: (isLoading: boolean) => void;
    setFooterRenderProp: (renderProp: (() => JSX.Element) | null) => void;
    scrollContainerRef: React.MutableRefObject<HTMLElement | undefined>;
    LineTemplate?: React.FC<LineTemplateProps>;
}

const BidirectionalLogView = (props: BidirectionalLogViewProps) => {
    const { logSource, filterString, setIsLoading, setFooterRenderProp, scrollContainerRef,
        LineTemplate = DefaultLineTemplate} = props;

    const { lines, isLoading, error, canContinueBackward, canContinueForward,
        fetchBeginning, fetchEnd, getNext, getPrev } = useLogStream(logSource, filterString);

    const { scrollToBottom, scrollToTop } = useScrollTracker(scrollContainerRef);

    const [lastPressedButton, setLastPressedButton] = useState<Buttons | null>(null);

    const onJumpToBeginning = useCallback(async () => {
        setLastPressedButton(Buttons.JumpToBeginning);
        await fetchBeginning();
        scrollToTop();
    }, [fetchBeginning, scrollToTop]);

    const onJumpToEnd = useCallback(async () => {
        setLastPressedButton(Buttons.JumpToEnd);
        await fetchEnd();
        scrollToBottom();
    }, [fetchEnd, scrollToBottom]);

    const onGetNext = useCallback(async () => {
        setLastPressedButton(Buttons.LoadNext);
        await getNext();
    }, [getNext]);

    const onGetPrev = useCallback(async () => {
        const prevScrollHeight = scrollContainerRef.current?.scrollHeight;

        setLastPressedButton(Buttons.LoadPrevious);
        await getPrev();

        // Yield to rendering so that the scroll container has a chance to update
        setTimeout(() => {
            // Check how much the scroll height has changed
            const diff = scrollContainerRef.current!.scrollHeight - prevScrollHeight!;

            // Restore to the previously visited last log line
            scrollContainerRef.current?.scrollTo(
                0,
                scrollContainerRef.current?.scrollTop + diff
            );
        }, 0);
    }, [getPrev, scrollContainerRef]);

    const renderNextButton = useCallback(() => {
        if (!canContinueForward) {
            return <></>;
        }

        return <StyledButton onClick={onJumpToEnd} disabled={isLoading}>{
            isLoading && lastPressedButton === Buttons.JumpToEnd ? loadingText : "jump to end"
        }</StyledButton>

    }, [canContinueForward, lastPressedButton, isLoading, onJumpToEnd]);

    useEffect(() => {
        fetchBeginning();
        // eslint-disable-next-line react-hooks/exhaustive-deps 
    }, []);

    useEffect(() => {
        setFooterRenderProp(renderNextButton);

        return () => {
            setFooterRenderProp(null);
        }
    }, [setFooterRenderProp, renderNextButton]);

    useEffect(() => {
        setIsLoading(isLoading);
    }, [isLoading, setIsLoading]);

    return <Container>
        {canContinueBackward && <>
            <JumpToBeginningButton onClick={onJumpToBeginning} disabled={isLoading} className={"jump-to-beginning"}>{
                isLoading && lastPressedButton === Buttons.JumpToBeginning ? loadingText : "jump to beginning"
            }</JumpToBeginningButton>
            <StyledButton onClick={onGetPrev} disabled={isLoading}>{
                isLoading && lastPressedButton === Buttons.LoadPrevious ? loadingText : "load previous"
            }</StyledButton>
        </>
        }
        <ScrollableContainer>
            {!!error && <Alert severity="error" sx={{ my: 5 }}>
                The server returned an error when asked for logs for this run.
            </Alert>}

            {lines.map((line, index) => (
                <LineTemplate key={index} index={index} line={line} />
            ))}
        </ScrollableContainer>
        {canContinueForward && <>
            <StyledButton onClick={onGetNext} disabled={isLoading}>{
                isLoading && lastPressedButton === Buttons.LoadNext ? loadingText : "load next"
            }</StyledButton>
        </>}
        {
            !canContinueForward && !isLoading && <Alert severity="info" sx={{ mt: 3 }}>
                {"No more matching lines"}
            </Alert>
        }
    </Container>;
};

interface LineTemplateProps {
    line: string;
    index: number;
}

export const DefaultLineTemplate = ({ line, index }: LineTemplateProps) => {
    const theme = useTheme();
    return <Box
        sx={{
            borderTop: 1,
            borderColor: theme.palette.grey[200],
            fontSize: 12,
            py: 2,
            pl: 1,
            color: theme.palette.grey[800],
            backgroundColor:
                index % 2 === 0 ? "white" : theme.palette.grey[50],
            paddingRight: 1
        }}
        key={index}
    >
        <code>{line}</code>
    </Box>;
}

const StyledConciseLine = styled(Box)`
    border-bottom: 1px solid ${theme.palette.grey[200]};

    &:nth-child(even) {
        background-color: ${theme.palette.grey[50]};
    }
`;

export const ConciseLineTemplate = ({ line, index }: LineTemplateProps) => {
    const theme = useTheme();
    return <StyledConciseLine
        sx={{
            fontSize: 12,
            color: theme.palette.grey[800],
            paddingRight: 1,
            paddingLeft: 5,
            minHeight: "25px",
            display: "flex",
            alignItems: "center"
        }}
        key={index}
    >
        <code>{line}</code>
    </StyledConciseLine>;
}

export default BidirectionalLogView
