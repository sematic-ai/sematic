import { useCallback, useEffect, useState } from "react";

const SCROLL_EVENTS = ["mousewheel", "DOMMouseScroll", "wheel", "MozMousePixelScroll"];

function _hasElementScrolledToBottom(refElement: HTMLElement | undefined) {
    if (!refElement) {
        return false;
    }
    const {scrollTop, clientHeight, scrollHeight } = refElement;

    return scrollHeight - scrollTop - clientHeight < 10;
};


export function useScrollTracker(
    refElement: React.MutableRefObject<HTMLElement | undefined>
) {
    
    const [hasReachedBottom, setHasReachedBottom] = useState(false);

    const checkHasScrolledToBottom = useCallback(() => {
        setHasReachedBottom(
            _hasElementScrolledToBottom(refElement.current)
        );
    }, [setHasReachedBottom, refElement]);

    const onScroll = useCallback(checkHasScrolledToBottom, [checkHasScrolledToBottom]);

    const scrollToBottom = useCallback(() => {
        const scroller = refElement.current;
        scroller?.scrollTo(0, scroller.scrollHeight);
        checkHasScrolledToBottom();
    }, [refElement, checkHasScrolledToBottom]);

    const scrollToTop = useCallback(() => {
        const scroller = refElement.current;
        scroller?.scrollTo(0, 0);
        checkHasScrolledToBottom();
    }, [refElement, checkHasScrolledToBottom]);

    useEffect(() => {
        const attachedDomElement = refElement.current;

        SCROLL_EVENTS.forEach(eventName => {
            attachedDomElement?.addEventListener(eventName, onScroll, {passive: true});
        });

        return () => {
            SCROLL_EVENTS.forEach(eventName => {
                attachedDomElement?.removeEventListener(eventName, onScroll);
            });
        };
    }, [refElement, onScroll]);

    return {
        hasReachedBottom,
        scrollToBottom,
        scrollToTop
    }
}
