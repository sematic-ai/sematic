import { useEffect, useState, useCallback, useMemo } from "react";
import { Box, Button, TextField } from "@mui/material";
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
  }>({ lines: [], cursor: null, source: logSource, filterString: "" });
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
      lineState.filterString != filterString ||
      lineState.lines.length === 0
    ) {
      next();
    }
  });

  const noMoreLinesIndicator = (
    <div className="no-more-indicator">
      ------ {currentNoLinesReason} ------
    </div>
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
    <div className="loading-overlay">
      <Loading error={undefined} isLoaded={false} />
      <p>{loadingMessage}</p>
    </div>
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
    <Box>
      <div className="ScrollingLogView">
        {overlay}
        <TextField
          fullWidth={true}
          className="filter"
          placeholder={"Filter..."}
          onChange={onFilterStringChange}
        />
        <div id={scrollerId} className="scroller">
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
              <div key={index}>{line}</div>
            ))}
          </InfiniteScroll>
        </div>
        <Button className="jump-to-end" onClick={accumulateUntilEnd}>
          Jump to end...
        </Button>
      </div>
    </Box>
  );
}
