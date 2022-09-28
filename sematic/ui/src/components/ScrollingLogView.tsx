import { useEffect, useState, useCallback } from "react";
import { Box } from "@mui/material";
import InfiniteScroll from "react-infinite-scroll-component";

export type MoreLinesCallback = (lines: string[], cursor: string | null, noLinesReason: string | null) => void;
export type GetLines = (cursor: string | null, moreLinesCallback: MoreLinesCallback) => void;

const DEFAULT_NO_LINES_REASON = "No more matching lines";

export default function ScrollingLogView(props: { getLines: GetLines, initialLines: string[], initialCursor: string | null, logSource: string}) {  
    const { getLines, initialLines, initialCursor, logSource } = props;

    const [existingLines, setLines] = useState<string[]>(initialLines);
    const [currentCursor, setCursor] = useState<string | null>(initialCursor);
    const [hasMore, setHasMore] = useState(true);
    const [currentNoLinesReason, setNoLinesReason] = useState<string | null>(DEFAULT_NO_LINES_REASON);

    const handleLogLines = useCallback((lines: string[], cursor: string | null, noLinesReason: string | null) => {
        var newLines: string[] = existingLines.concat(lines);
        setLines(newLines);
        setCursor(cursor);
        setHasMore(cursor != null);
        setNoLinesReason(noLinesReason === "" || noLinesReason === null? DEFAULT_NO_LINES_REASON : noLinesReason);
    }, [existingLines]);

    const next = useCallback(() => {
        getLines(currentCursor, handleLogLines);
    }, [getLines, currentCursor, handleLogLines]);

    useEffect(() => {
        setCursor(null);
        setLines([]);
        setHasMore(true);
        next();
    }, [logSource]);

    const noMoreLinesIndicator = (
        <div className="no-more-indicator">------ {currentNoLinesReason} ------</div>
    );
    const scrollerId = "scrolling-logs-" + logSource;

    return (
      <Box>
          <div id={scrollerId} className="ScrollingLogView">
            <InfiniteScroll
                dataLength={existingLines.length}
                next={next}
                scrollableTarget={scrollerId}
                hasMore={hasMore}
                loader={<h4>Loading...</h4>}
                endMessage={noMoreLinesIndicator}
            >
                {
                    existingLines.map((line, index) => (
                        <div key={index}>{line}</div>
                    ))
                }
            </InfiniteScroll>
          </div>
      </Box>
    );
  }
