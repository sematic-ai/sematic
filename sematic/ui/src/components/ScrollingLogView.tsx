import { useEffect, useState, useCallback, useMemo } from "react";
import { Alert, Box, Button, TextField, useTheme } from "@mui/material";
import InfiniteScroll from "react-infinite-scroll-component";
import Loading from "./Loading";

// Callback to be used when more log lines are loaded.
export type MoreLinesCallback = (
  source: string,
  usedFilter: string,
  lines: string[],
  cursor: string | null,
  noLinesReason: string | null
) => void;

// Function to get more logs. It should call moreLinesCallback
// once it has more log lines.
export type GetLines = (
  source: string,
  cursor: string | null,
  filterString: string,
  moreLinesCallback: MoreLinesCallback
) => void;

const DEFAULT_NO_LINES_REASON = "No more matching lines";

export default function ScrollingLogView(props: {
  getLines: GetLines;
  logSource: string;
}) {
  const { getLines, logSource } = props;
  const theme = useTheme();
  const [hasMore, setHasMore] = useState(true);
  const [fastForwarding, setFastForwarding] = useState(false);
  const [currentNoLinesReason, setNoLinesReason] = useState<string | null>(
    DEFAULT_NO_LINES_REASON
  );
  const [loadingMessage, setLoadingMessage] = useState<string>("Loading...");

  const [lineState, setLineState] = useState<{
    lines: string[]; // the log lines themselves
    cursor: string | null; // the cursor to continue getting the lines after these ones
    source: string; // the id of the source these log lines are for
    filterString: string; // the filter string that was used to produce these lines

    // initialize the state to no logs from an unknown source/filter.
    // An on-render effect will do the first load from the actual source.
  }>({ lines: [], cursor: null, source: "", filterString: "" });

  const [filterString, setFilterString] = useState<string>("");

  // display log lines once they have been loaded from the server.
  const handleLogLines = useCallback(
    (
      source: string,
      usedFilter: string,
      lines: string[],
      cursor: string | null,
      noLinesReason: string | null
    ) => {
      const newSource =
        source !== lineState.source || usedFilter !== lineState.filterString;
      var newLines: string[] = newSource
        ? lines
        : lineState.lines.concat(lines);
      setLineState({
        ...lineState,
        lines: newLines,
        cursor: cursor,
        source: source,
        filterString: usedFilter,
      });
      setHasMore(cursor != null);
      setNoLinesReason(
        noLinesReason === "" || noLinesReason === null
          ? DEFAULT_NO_LINES_REASON
          : noLinesReason
      );
    },
    [lineState]
  );

  // load the next log lines after the ones currently being displayed
  const next = useCallback(() => {
    const sameSource =
      lineState.source === logSource && lineState.filterString === filterString;
    getLines(
      logSource,
      sameSource ? lineState.cursor : null,
      filterString,
      handleLogLines
    );
  }, [getLines, lineState.cursor, handleLogLines, logSource, filterString]);

  // on render: if the current lines didn't come from the source & filter that
  // are currently set, load new logs with the current settings.
  useEffect(() => {
    if (
      lineState.source !== logSource ||
      lineState.filterString !== filterString
    ) {
      next();
    }
  });

  const noMoreLinesIndicator = (
    <Alert severity="info" sx={{ mt: 3 }}>
      {currentNoLinesReason}
    </Alert>
  );
  const scrollerId = "scrolling-logs-" + lineState.source;

  // repeatedly query the server until we have loaded as many log lines as
  // it will give us.
  const accumulateUntilEnd = useCallback(() => {
    if (lineState.lines.length === 0) {
      // run has no logs. No need to try to scroll to the end.
      return;
    }
    setFastForwarding(true);
    var accumulatedLines: string[] = [];
    const accumulate = function (
      source: string,
      usedFilter: string,
      lines: string[],
      cursor: string | null,
      noLinesReason: string | null
    ) {
      accumulatedLines.push(...lines);
      if (
        (cursor === null || lines.length === 0) &&
        accumulatedLines.length > 0
      ) {
        setLoadingMessage("Rendering...");

        setFastForwarding(false);
        handleLogLines(
          source,
          usedFilter,
          accumulatedLines,
          cursor,
          noLinesReason
        );

        // start the scroll-to-bottom asynchronously so the lines have time
        // to actually render before it scrolls.
        setTimeout(() => {
          const scroller = document.getElementById(scrollerId);
          scroller?.scrollTo(0, scroller.scrollHeight);
        }, 0);
      } else {
        setLoadingMessage("Loaded " + accumulatedLines.length + " lines...");
        getLines(source, cursor, usedFilter, accumulate);
      }
    };
    accumulate(logSource, filterString, [], null, null);
  }, [getLines, handleLogLines, logSource, scrollerId]);

  // scroll to the bottom when fast forwarding/jumping to end is done
  useMemo(() => {
    if (!fastForwarding) {
      const scroller = document.getElementById(scrollerId);
      scroller?.scrollTo(0, scroller.scrollHeight);
    }
  }, [fastForwarding, scrollerId]);

  // overlay with the load spinner and loading text while we are jumping to the end
  const overlay = fastForwarding ? (
    <Box
      sx={{
        zIndex: 100,
        left: 0,
        top: 0,
        position: "absolute",
        height: "100%",
        width: "100%",
        backgroundColor: "white",
        opacity: 0.8,
        textAlign: "center",
      }}
    >
      <Loading error={undefined} isLoaded={false} />
      <p>{loadingMessage}</p>
    </Box>
  ) : (
    <div></div>
  );

  const onFilterStringChange = useCallback(
    (evt: any) => {
      setFilterString(evt.target.value);
    },
    [filterString, next]
  );

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
      if (lineState.cursor !== null && distanceFromScrollBottom < 1000) {
        next();
      }
    },
    [filterString, next]
  );

  return (
    <Box sx={{ mt: 5, position: "relative", left: 0, top: 0 }}>
      {overlay}
      <TextField
        variant="standard"
        fullWidth={true}
        placeholder={"Filter..."}
        onChange={onFilterStringChange}
      />
      <Box id={scrollerId} sx={{ height: "40hv", my: 5, pt: 1 }}>
        <InfiniteScroll
          dataLength={lineState.lines.length}
          next={next}
          scrollableTarget={scrollerId}
          hasMore={hasMore}
          loader={<h4>Loading...</h4>}
          onScroll={onScroll}
          endMessage={noMoreLinesIndicator}
        >
          {lineState.lines.map((line, index) => (
            <Box
              sx={{
                borderTop: 1,
                borderColor: theme.palette.grey[200],
                fontSize: 12,
                py: 2,
                color: theme.palette.grey[800],
                backgroundColor:
                  index % 2 == 0 ? "white" : theme.palette.grey[50],
              }}
              key={index}
            >
              <code>{line}</code>
            </Box>
          ))}
        </InfiniteScroll>
      </Box>
      {hasMore && (
        <Button onClick={accumulateUntilEnd} sx={{ width: "100%" }}>
          Jump to end...
        </Button>
      )}
    </Box>
  );
}
