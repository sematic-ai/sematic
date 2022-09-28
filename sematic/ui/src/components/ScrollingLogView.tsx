import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Box, Button } from "@mui/material";
import InfiniteScroll from "react-infinite-scroll-component";

export type MoreLinesCallback = (lines: string[], cursor: string | null, noLinesReason: string | null) => void;
export type GetLines = (cursor: string | null, moreLinesCallback: MoreLinesCallback) => void;

const DEFAULT_NO_LINES_REASON = "No more matching lines";

export default function ScrollingLogView(props: { getLines: GetLines, initialLines: string[], initialCursor: string | null}) {  
    const { getLines, initialLines, initialCursor } = props;

    const [existingLines, setLines] = useState<string[]>(initialLines);
    const [currentCursor, setCursor] = useState<string | null>(initialCursor);
    const [hasMore, setHasMore] = useState(true);
    const [currentNoLinesReason, setNoLinesReason] = useState<string | null>(DEFAULT_NO_LINES_REASON);

    const handleLogLines = (lines: string[], cursor: string | null, noLinesReason: string | null) => {
        var newLines: string[] = existingLines.concat(lines);
        setLines(newLines);
        setCursor(cursor);
        setHasMore(cursor != null);
        if (cursor == null) {
            // there's no more to display
            setNoLinesReason(DEFAULT_NO_LINES_REASON);
        } else {
            setNoLinesReason(noLinesReason);
        }
    };

    const next = () => {
        getLines(currentCursor, handleLogLines);
    };

    useMemo(() => {
        setLines([]);
        setCursor(null);
        setHasMore(true);
        next();
    }, [getLines]);

    const noMoreLinesIndicator = (
        <div className="no-more-indicator">------ {currentNoLinesReason} ------</div>
    );

    return (
      <Box>
          <div id="scrolling-logs" className="ScrollingLogView">
            <InfiniteScroll
                dataLength={existingLines.length}
                next={next}
                scrollableTarget="scrolling-logs"
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
