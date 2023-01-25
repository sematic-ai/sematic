import { useEffect, useCallback, useMemo } from "react";
import { Alert, Box, Button, LinearProgress, useTheme } from "@mui/material";
import ArrowCircleDownIcon from '@mui/icons-material/ArrowCircleDown';
import InfiniteScroll from "react-infinite-scroll-component";
import { useAccumulateLogsUntilEnd, useLogStream } from "../hooks/logHooks";
import { usePulldownTrigger, useScrollTracker } from "../hooks/scrollingHooks";
import { ExceptionMetadata } from "../Models";
import { Exception, ExternalException } from "../components/Exception";
import usePrevious from "react-use/lib/usePrevious";
import { useRunPanelContext } from "../hooks/runDetailsHooks";
import { styled } from "@mui/system";

const DEFAULT_LOG_INFO_MESSAGE = "No more matching lines";

const FooterContainer = styled(Box)(({theme}) => ({
  backgroundColor: theme.palette.background.paper
}));

export default function ScrollingLogView(props: {
  logSource: string;
  filterString: string;
  external_exception_metadata_json: ExceptionMetadata | null;
  exception_metadata_json: ExceptionMetadata | null;
}) {
  const { logSource, filterString, external_exception_metadata_json, 
    exception_metadata_json } = props;
  const theme = useTheme();

  // Single pull logic
  const { lines, isLoading, error: logLoadError, hasMore, 
    logInfoMessage, getNext, hasPulledData } = useLogStream(logSource, filterString);

  // Accumulator (logs draining) logic
  const { accumulateLogsUntilEnd, isLoading: isAccumulatorLoading,
    isAccumulating, accumulatedLines } = useAccumulateLogsUntilEnd(hasMore, getNext);

  const { setFooterRenderProp, scrollerId, scrollContainerRef, setIsLoading } = useRunPanelContext();

  
  const pullDownCallback = useCallback(async () => {
    if (isAccumulating || isLoading || !hasMore) {
      return;
    }
    await getNext();
  }, [isAccumulating, isLoading, getNext, hasMore]);

  const {pullDownProgress, pullDownTriggerEnabled} 
    = usePulldownTrigger(scrollContainerRef!, pullDownCallback);

  const infiniteScrollGetNext = useCallback(() => {
    // If the accumulator is under way, don't initiate a pull 
    // from the <InfiniteScroll />
    if (isAccumulating) {
      return;
    }
    getNext();
  }, [getNext, isAccumulating]);

  const { hasReachedBottom, scrollToBottom } = useScrollTracker(scrollContainerRef);


  const logInfoMessageBanner = useMemo(() =>
    <Alert severity="info" sx={{ mt: 3 }}>
      {isLoading? "Loading..." : (logInfoMessage || DEFAULT_LOG_INFO_MESSAGE)}
    </Alert>
    , [logInfoMessage, isLoading]);

  const accumulatorButtonMessage = useMemo(() => {
    if (!isAccumulating && hasMore) {
      return "Jump to the end";
    }
    if (isAccumulatorLoading) {
      return `Loaded ${accumulatedLines} lines...`;
    }
    return "Rendering...";
  }, [isAccumulating, isAccumulatorLoading, accumulatedLines, hasMore]);

  const pullDownTriggerSection = useMemo(() => {
    if (!pullDownTriggerEnabled || isAccumulating || !hasMore) {
      return <></>;
    }
    return (<>
      <Alert severity="info" icon={<ArrowCircleDownIcon fontSize="inherit" />}>
        Keep scrolling down to get more logs
      </Alert>
      {/* The progress bar is visual feedback for user interaction. It tells the user
        * how much more to scroll to trigger log fetching. It urges the user to keep 
        * scrolling down if re-fetching is what the user desires. 
        * 
        * It is not a loading indicator for I/O transmission like the spinner.
        */}
      <LinearProgress value={Math.floor(pullDownProgress)} variant={"determinate"}
      sx={{
        '& .MuiLinearProgress-bar': {
          'transitionDuration': '10ms'
        }
      }} />
    </>);
  }, [pullDownTriggerEnabled, pullDownProgress, isAccumulating, hasMore]);

  const prevIsAccumulating = usePrevious(isAccumulating);

  const renderNextButton = useCallback(() => {
    return <FooterContainer>
      {(hasMore && 
        <Button
          onClick={accumulateLogsUntilEnd}
          sx={{ width: "100%" }}
          disabled={isAccumulating || isLoading}
          style={{flexShrink: 1}}
        >
          {accumulatorButtonMessage}
        </Button>
      )}
      {
        (!hasMore && !hasReachedBottom && 
          <Button
            onClick={scrollToBottom}
            sx={{ width: "100%" }}
            style={{flexShrink: 1}}
          >
            "Jump to the end"
          </Button>)
      }
    </FooterContainer>;
  }, [hasMore, hasReachedBottom, isAccumulating, isLoading, 
    accumulatorButtonMessage, scrollToBottom, accumulateLogsUntilEnd]);

  useEffect(()=> {
    setFooterRenderProp(renderNextButton);

    return () => {
      setFooterRenderProp(null);
    }
  }, [setFooterRenderProp, renderNextButton]);

  // scroll to the bottom when fast forwarding/jumping to end 
  // (aka accumulating) has gotten data
  useEffect(() => {
    if (prevIsAccumulating === true && isAccumulatorLoading === false) {
      scrollToBottom();
    }
  }, [prevIsAccumulating, isAccumulatorLoading, scrollToBottom]);

  useEffect(() => {
    const hasContainerScrolled = scrollContainerRef.current!.scrollTop > 0;
    // If <InfiniteScroll /> has not scrolled, the initial pull will not be triggered
    // this drives an initial data pull.
    // If <InfiniteScroll /> has scrolled, the initial pull will be triggered by the 
    // component itself.
    if (!hasPulledData && !hasContainerScrolled) { 
      getNext();
    }
  }, [getNext, hasPulledData, scrollContainerRef]);

  useEffect(() => {
    setIsLoading(isLoading);
    return () => {
      setIsLoading(false);
    }
  }, [setIsLoading, isLoading]);

  return (
    <>
      <Box
        sx={{
          mt: 1.5,
          pt: 1,
          whiteSpace: "break-spaces",
          overflowY: "visible",
          width: `100%`,
          lineBreak: 'anywhere',
          flexGrow: 1,
        }}
      >
        <InfiniteScroll
          dataLength={lines.length}
          next={infiniteScrollGetNext}
          scrollableTarget={scrollerId}
          hasMore={hasMore}
          loader={null}
          endMessage={logInfoMessageBanner}
        >
          {external_exception_metadata_json && <Box sx={{ paddingBottom: 4, }} >
            <ExternalException
              exception_metadata={external_exception_metadata_json} />
          </Box>}

          {exception_metadata_json && <Box sx={{ paddingBottom: 4, }} >
            <Exception exception_metadata={exception_metadata_json} /></Box>}
          
          {logLoadError!! && <Alert severity="error" sx={{ my: 5 }}>
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
        </InfiniteScroll>
        <div style={{width: '100%', height: '60px', margin: '0.5em 0'}}>
          {pullDownTriggerSection}
        </div>
      </Box>
    </>
  );
}
