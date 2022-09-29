import { useEffect, useState, useCallback } from "react";
import { Box, Button } from "@mui/material";
import InfiniteScroll from "react-infinite-scroll-component";
import Loading from "./Loading";

export type MoreLinesCallback = (
  lines: string[],
  cursor: string | null,
  noLinesReason: string | null
) => void;
export type GetLines = (
  cursor: string | null,
  moreLinesCallback: MoreLinesCallback
) => void;

const DEFAULT_NO_LINES_REASON = "No more matching lines";

export default function ScrollingLogView(props: {
  getLines: GetLines;
  initialLines: string[];
  initialCursor: string | null;
  logSource: string;
}) {
  const { getLines, initialLines, initialCursor, logSource } = props;

  const [existingLines, setLines] = useState<string[]>(initialLines);
  const [currentCursor, setCursor] = useState<string | null>(initialCursor);
  const [hasMore, setHasMore] = useState(true);
  const [fastForwarding, setFastForwarding] = useState(false);
  const [currentNoLinesReason, setNoLinesReason] = useState<string | null>(
    DEFAULT_NO_LINES_REASON
  );
  const [loadingMessage, setLoadingMessage] = useState<string>("Loading...");

  const handleLogLines = useCallback(
    (lines: string[], cursor: string | null, noLinesReason: string | null) => {
      var newLines: string[] = fastForwarding
        ? lines
        : existingLines.concat(lines);
      setLines(newLines);
      setCursor(cursor);
      setHasMore(cursor != null);
      setNoLinesReason(
        noLinesReason === "" || noLinesReason === null
          ? DEFAULT_NO_LINES_REASON
          : noLinesReason
      );
    },
    [existingLines, logSource, fastForwarding]
  );

  const next = useCallback(() => {
    getLines(currentCursor, handleLogLines);
  }, [getLines, currentCursor, handleLogLines, logSource]);

  useEffect(() => {
    setCursor(null);
    setLines([]);
    setHasMore(true);
    next();
  }, [logSource]);

  const noMoreLinesIndicator = (
    <div className="no-more-indicator">
      ------ {currentNoLinesReason} ------
    </div>
  );
  const scrollerId = "scrolling-logs-" + logSource;

  const accumulateUntilEnd = () => {
    var accumulatedLines: string[] = [];
    const accumulate = function (
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

        // Set fast-forwarding to false asynchronously so
        // it has time to render the lines before it removes
        // the overlay.
        setTimeout(() => setFastForwarding(false), 0);

        handleLogLines(accumulatedLines, cursor, noLinesReason);
      } else {
        setLoadingMessage("Loaded " + accumulatedLines.length + " lines...");
        setTimeout(() => getLines(cursor, accumulate), 0);
      }
    };
    accumulate([], null, null);
  };

  const jumpToEnd = () => {
    setFastForwarding(true);
    accumulateUntilEnd();
  };

  useEffect(() => {
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
            dataLength={existingLines.length}
            next={next}
            scrollableTarget={scrollerId}
            hasMore={hasMore}
            loader={<h4>Loading...</h4>}
            endMessage={noMoreLinesIndicator}
          >
            {existingLines.map((line, index) => (
              <div key={index}>{line}</div>
            ))}
          </InfiniteScroll>
        </div>
        <Button className="jump-to-end" onClick={jumpToEnd}>
          Jump to end...
        </Button>
      </div>
    </Box>
  );
}
