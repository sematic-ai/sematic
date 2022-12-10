import { useEffect, useCallback, useMemo } from "react";
import { Alert, Box, Button, useTheme } from "@mui/material";
import InfiniteScroll from "react-infinite-scroll-component";
import Loading from "./Loading";
import { useAccumulateLogsUntilEnd, useLogStream } from "../hooks/logHooks";

const DEFAULT_NO_LINES_REASON = "No more matching lines";

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
    noMoreLinesReason, getNext, hasPulledData } = useLogStream(logSource, filterString);
  
  // Accumulator (logs draining) logic
  const { accumulateLogsUntilEnd, isLoading: isAccumulatorLoading,
    isAccumulating, accumulatedLines } = useAccumulateLogsUntilEnd(hasMore, getNext);
  
  // report to parent in case of errors.
  useEffect(()=> {
    if (!!error) {
      onError(error);
    }
  }, [onError, error])

  const onScroll = useCallback(
    (evt: any) => {
      // when the user is scrolling near the last line, and there might still
      // be more lines, we want to refresh. This is a distinct situation from
      // the normal "infinite scroll" because the normal infinite scroll will
      // only do one "next" when near the bottom and not do another if it didn't
      // get more lines. We still want to leave the normal infinite scroll on though:
      // it makes it so if a user is scrolling, we pre-emptively load the end before
      // the user gets too close to it which will provide a smoother experience.
      const distanceFromScrollBottom =
        evt.target.scrollHeight - evt.target.scrollTop;
      if (hasMore && distanceFromScrollBottom < 100) {
        getNext();
      }
    },
    [getNext, hasMore]
  );

  const infiniteScrollGetNext = useCallback(() => {
    // If the accumulator is under way, don't initiate a pull 
    // from the <InfiniteScroll />
    if (isAccumulating) {
      return;
    }
    getNext();
  }, [getNext, isAccumulating]);

  const noMoreLinesIndicator = useMemo(() =>
    <Alert severity="info" sx={{ mt: 3 }}>
      {isLoading? "Loading..." : (noMoreLinesReason || DEFAULT_NO_LINES_REASON)}
    </Alert>
    , [noMoreLinesReason, isLoading]);

  const accumulatorButtonMessage = useMemo(() => {
    if (!isAccumulating && hasMore) {
      return "Jump to the end";
    }
    if (isAccumulatorLoading) {
      return `Loaded ${accumulatedLines} lines...`;
    }
    return "Rendering...";
  }, [isAccumulating, isAccumulatorLoading, accumulatedLines, hasMore]);

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
    <Box
      sx={{
        mt: 5,
        position: "relative",
        left: 0,
        top: 0,
      }}
    >
      
      <Box
        id={scrollerId}
        sx={{
          height: "400px",
          my: 5,
          pt: 1,
          whiteSpace: "nowrap",
          overflow: "hidden",
          overflowY: "scroll",
          gridRow: 2,
        }}
      >
        <InfiniteScroll
          dataLength={lines.length}
          next={infiniteScrollGetNext}
          scrollableTarget={scrollerId}
          hasMore={hasMore}
          loader={<Loading isLoaded={!isLoading} />}
          onScroll={onScroll}
          endMessage={noMoreLinesIndicator}
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
              }}
              key={index}
            >
              <code>{line}</code>
            </Box>
          ))}
        </InfiniteScroll>
      </Box>
      {(hasMore && 
        <Button
          onClick={accumulateLogsUntilEnd}
          sx={{ width: "100%" }}
          disabled={isAccumulating || isLoading}
        >
          {accumulatorButtonMessage}
        </Button>
      )}
    </Box>
  );
}
