import { useEffect, useState, useCallback, useMemo } from "react";
import { Box, Button, TextField } from "@mui/material";
import InfiniteScroll from "react-infinite-scroll-component";
import Loading from "./Loading";

export type MoreLinesCallback = (
  source: string,
  usedFilter: string,
  lines: string[],
  cursor: string | null,
  noLinesReason: string | null
) => void;
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

  const accumulateUntilEnd = useCallback(() => {
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

  useMemo(() => {
    // scroll to the bottom when fast forwarding is done
    if (!fastForwarding) {
      const scroller = document.getElementById(scrollerId);
      scroller?.scrollTo(0, scroller.scrollHeight);
    }
  }, [fastForwarding, scrollerId]);

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
