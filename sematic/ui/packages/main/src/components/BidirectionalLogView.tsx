import { useCallback, useEffect, useState } from "react";
import { useLogStream } from "src/hooks/logHooks";
import styled from "@emotion/styled";
import Box from "@mui/material/Box";
import { useTheme } from "@mui/material/styles";
import Alert from "@mui/material/Alert";
import { useRunPanelContext, useRunPanelLoadingIndicator } from "src/hooks/runDetailsHooks";
import { Button } from "@mui/material";
import { theme } from "@sematic/common/lib/src/theme/mira";
import { useScrollTracker } from "src/hooks/scrollingHooks";

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
    top: 118px;
`;

enum Buttons {
    JumpToBeginning,
    JumpToEnd,
    LoadPrevious,
    LoadNext
}

const loadingText = 'loading...';
interface BidirectionalLogViewProps {
    logSource: string;
    filterString: string;
}

const BidirectionalLogView = (props: BidirectionalLogViewProps) => {
    const { logSource, filterString } = props;

    const theme = useTheme();

    const { setFooterRenderProp, scrollContainerRef } = useRunPanelContext();

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
            isLoading && lastPressedButton === Buttons.JumpToEnd ? loadingText : 'jump to end'
        }</StyledButton>

    }, [canContinueForward, lastPressedButton, isLoading, onJumpToEnd]);

    useRunPanelLoadingIndicator(isLoading);

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

    return <Container>
        {canContinueBackward && <>
            <JumpToBeginningButton onClick={onJumpToBeginning} disabled={isLoading}>{
                isLoading && lastPressedButton === Buttons.JumpToBeginning ? loadingText : 'jump to beginning'
            }</JumpToBeginningButton>
            <StyledButton onClick={onGetPrev} disabled={isLoading}>{
                isLoading && lastPressedButton === Buttons.LoadPrevious ? loadingText : 'load previous'
            }</StyledButton>
        </>
        }
        <ScrollableContainer>
            {!!error && <Alert severity="error" sx={{ my: 5 }}>
                The server returned an error when asked for logs for this run.
            </Alert>}

            {lines.map((line, index) => (
                <Box
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
                </Box>
            ))}
        </ScrollableContainer>
        {canContinueForward && <>
            <StyledButton onClick={onGetNext} disabled={isLoading}>{
                isLoading && lastPressedButton === Buttons.LoadNext ? loadingText : 'load next'
            }</StyledButton>
        </>}
        {
            !canContinueForward && !isLoading && <Alert severity="info" sx={{ mt: 3 }}>
                {"No more matching lines"}
            </Alert>
        }
    </Container>;
};

export default BidirectionalLogView
