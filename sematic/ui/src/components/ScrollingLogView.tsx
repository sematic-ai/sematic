import { useEffect, useCallback, useMemo, useRef } from "react";
import { Alert, Box, Button, LinearProgress, useTheme } from "@mui/material";
import ArrowCircleDownIcon from '@mui/icons-material/ArrowCircleDown';
import InfiniteScroll from "react-infinite-scroll-component";
import Loading from "./Loading";
import { useAccumulateLogsUntilEnd, useLogStream } from "../hooks/logHooks";
import { usePulldownTrigger } from "../hooks/scrollingHooks";

const DEFAULT_LOG_INFO_MESSAGE = "No more matching lines";

export default function ScrollingLogView(props: {
  logSource: string;
  filterString: string;
  onError: (error: Error) => void
}) {
  const { logSource, filterString, onError } = props;
  const theme = useTheme();

  const scrollerId = useMemo(() => `scrolling-logs-${logSource}`, [logSource]) ;

  // Single pull logic
  const { lines, isLoading, error, hasMore, 
    logInfoMessage, getNext, hasPulledData } = useLogStream(logSource, filterString);
  
  // Accumulator (logs draining) logic
  const { accumulateLogsUntilEnd, isLoading: isAccumulatorLoading,
    isAccumulating, accumulatedLines } = useAccumulateLogsUntilEnd(hasMore, getNext);
  
  // report to parent in case of errors.
  useEffect(()=> {
    if (!!error) {
      onError(error);
    }
  }, [onError, error]);

  const scrollMonitorRef = useRef<HTMLElement>();

  const pullDownCallback = useCallback(async () => {
    if (isAccumulating || isLoading || !hasMore) {
      return;
    }
    await getNext();
  }, [isAccumulating, isLoading, getNext]);

  const {pullDownProgress, pullDownTriggerEnabled} 
    = usePulldownTrigger(scrollMonitorRef!, pullDownCallback);

  const infiniteScrollGetNext = useCallback(() => {
    // If the accumulator is under way, don't initiate a pull 
    // from the <InfiniteScroll />
    if (isAccumulating) {
      return;
    }
    getNext();
  }, [getNext, isAccumulating]);

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

  // scroll to the bottom when fast forwarding/jumping to end 
  // (aka accumulating) has gotten data
  useEffect(() => {
    if (!isAccumulatorLoading) {
      const scroller = document.getElementById(scrollerId);
      scroller?.scrollTo(0, scroller.scrollHeight);
    }
  }, [isAccumulatorLoading, scrollerId]);

  useEffect(() => {
    // not sure why <InfiniteScroll /> does not do an initial pull,
    // this mitigates that issue.
    if (!hasPulledData) { 
      getNext();
    }
  }, [getNext, hasPulledData]);

  return (
    <>
      <Box
        id={scrollerId}
        ref={scrollMonitorRef}
        sx={{
          height: 0,
          mt: 5,
          pt: 1,
          whiteSpace: "break-spaces",
          overflow: "hidden",
          overflowY: "scroll",
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
          loader={<Loading isLoaded={!isLoading} />}
          endMessage={logInfoMessageBanner}
        >
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
        <div style={{width: '100%', height: '40px', margin: '0.5em 0'}}>
          {pullDownTriggerSection}
        </div>
      </Box>
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
    </>
  );
}
