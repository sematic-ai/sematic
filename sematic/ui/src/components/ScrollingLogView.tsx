import { useEffect, useState, useCallback, useMemo } from "react";
import { Box, Button } from "@mui/material";
import InfiniteScroll from "react-infinite-scroll-component";
import Loading from "./Loading";

export type MoreLinesCallback = (
  source: string,
  lines: string[],
  cursor: string | null,
  noLinesReason: string | null
) => void;
export type GetLines = (
  source: string,
  cursor: string | null,
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

  const [state, setState] = useState<{
    lines: string[];
    cursor: string | null;
    source: string;
  }>({ lines: [], cursor: null, source: logSource });

  const handleLogLines = useCallback(
    (
      source: string,
      lines: string[],
      cursor: string | null,
      noLinesReason: string | null
    ) => {
      var newLines: string[] =
        source === state.source ? state.lines.concat(lines) : lines;
      setState({
        ...state,
        lines: newLines,
        cursor: cursor,
        source: source,
      });
      setHasMore(cursor != null);
      setNoLinesReason(
        noLinesReason === "" || noLinesReason === null
          ? DEFAULT_NO_LINES_REASON
          : noLinesReason
      );
    },
    [state]
  );

  const next = useCallback(() => {
    getLines(logSource, state.cursor, handleLogLines);
  }, [getLines, state.cursor, handleLogLines, logSource]);

  useEffect(() => {
    if (state.source !== logSource || state.lines.length === 0) {
      next();
    }
  });

  const noMoreLinesIndicator = (
    <div className="no-more-indicator">
      ------ {currentNoLinesReason} ------
    </div>
  );
  const scrollerId = "scrolling-logs-" + state.source;

  const accumulateUntilEnd = useCallback(() => {
    setFastForwarding(true);
    var accumulatedLines: string[] = [];
    const accumulate = function (
      source: string,
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
        handleLogLines(source, accumulatedLines, cursor, noLinesReason);

        // start the scroll-to-bottom asynchronously so the lines have time
        // to actually render before it scrolls.
        setTimeout(() => {
          const scroller = document.getElementById(scrollerId);
          scroller?.scrollTo(0, scroller.scrollHeight);
        }, 0);
      } else {
        setLoadingMessage("Loaded " + accumulatedLines.length + " lines...");
        getLines(source, cursor, accumulate);
      }
    };
    accumulate(logSource, [], null, null);
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

  return (
    <Box>
      <div className="ScrollingLogView">
        {overlay}
        <div id={scrollerId} className="scroller">
          <InfiniteScroll
            dataLength={state.lines.length}
            next={next}
            scrollableTarget={scrollerId}
            hasMore={hasMore}
            loader={<h4>Loading...</h4>}
            endMessage={noMoreLinesIndicator}
          >
            {state.lines.map((line, index) => (
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
