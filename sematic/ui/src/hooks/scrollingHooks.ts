import { useCallback, useEffect, useRef, useState } from "react";
import { useLogger } from "../utils";
import { useSetTimeout } from "./setTimeoutHooks";

const SCROLL_EVENTS = ['mousewheel', 'DOMMouseScroll', 'wheel', 'MozMousePixelScroll'];
const SCROLL_DOWN_CONTINUATION = 800;

function _hasElementScrolledToBottom(refElement: HTMLElement | undefined) {
    if (!refElement) {
        return false;
    }
    const {scrollTop, clientHeight, scrollHeight } = refElement;

    return scrollHeight - scrollTop - clientHeight < 10;
};
/**
 * A hook tracks that whether `refElement` has scrolled down to the bottom,
 * and then user has kept scrolling down for SCROLL_DOWN_CONTINUATION consecutive
 * milliseconds. If so, `callback` will be triggered.
 * 
 * @param refElement The scrolling container to monitor. Its height should be 
 *        taller than its content's height. (or there will be no scrolling)
 * @param callback The callback to call.
 * @returns 
 */
export function usePulldownTrigger(
    refElement: React.MutableRefObject<HTMLElement | undefined>,
    callback: () => Promise<void>
) {
    const { devLogger } = useLogger();
    const hasElementScrolledToBottom = useCallback(() => {
        return _hasElementScrolledToBottom(refElement.current);
    }, [refElement]);

    const [pullDownTriggerEnabled, setPullDownTriggerEnabled] = useState(false);
    const [markPulldownTriggerEnabled, cancelPulldownTriggerEnabled] = useSetTimeout(useCallback(() => {
        // Mark the `enabled` state only when the scrolling has completely ceased.
        // (in other words, there is not another follow-up scroll event to cancel this marking.)
        setPullDownTriggerEnabled(true);
    }, [setPullDownTriggerEnabled]), 50);

    // This timeout function cancels the above timeout function
    const [startDroppingPulldownTrigger, cancelDroppingPulldownTrigger] = useSetTimeout(() => {
        cancelPulldownTriggerCall();
        setPulldownProgress(0);
    }, SCROLL_DOWN_CONTINUATION *.3);

    // This is the timeout function who eventually trigger the `callback`
    const [startPullDownTriggerCall, 
        cancelPulldownTriggerCall, 
        isPullDownTriggerCallInitiated
    ] = useSetTimeout(useCallback(async () => {
        setPulldownProgress(100);
        devLogger('Pulldown triggered');
        cancelDroppingPulldownTrigger();
        pulldownCallbackInprogress.current = true;

        await callback();
        devLogger('Pulled down callback completed');

        setPulldownProgress(0);
        pulldownCallbackInprogress.current = false;
    }, [callback, cancelDroppingPulldownTrigger, devLogger]), SCROLL_DOWN_CONTINUATION);

    
    const pullDownTriggerStarttime = useRef<number>(0);
    const pulldownCallbackInprogress = useRef<boolean>(false);

    const [pullDownProgress, setPulldownProgress] = useState<number>(0);

    const onScroll = useCallback((event: Event) => {
        if (pulldownCallbackInprogress.current) {
            return;
        }
        event.stopPropagation();

        // Phase 1: detect whether the scrolling has reached to the bottom
        const hasReachedBottom = hasElementScrolledToBottom();
        cancelPulldownTriggerEnabled();

        if (hasReachedBottom) {
            if (!pullDownTriggerEnabled) {
                // mark pulldown trigger enabled in a delayed way.
                markPulldownTriggerEnabled();
            }
        } else {
            setPullDownTriggerEnabled(false);
        }

        if (!pullDownTriggerEnabled) {
            return false;
        }

        // Phase 2: detect whether there is a continous scrolling down for 
        // SCROLL_DOWN_CONTINUATION milliseconds. If it has, then `callback`
        // will be triggered.
        const { deltaY } = event as WheelEvent;
        if (deltaY >= 0) { // deltaY >= 0 means it is scrolling down
            // initiate pulldown trigger if not yet
            if (!isPullDownTriggerCallInitiated()) {
                setPulldownProgress(0);
                startPullDownTriggerCall();
                pullDownTriggerStarttime.current = performance.now();
            }
            // cancel previous attempt of cancelling pulldown trigger, so
            // the cancellation of pulldownTrigger is delayed.
            cancelDroppingPulldownTrigger();
            
            setPulldownProgress(
                (performance.now() - pullDownTriggerStarttime.current) / SCROLL_DOWN_CONTINUATION * 100
            );

            // prepare to cancel pulldown trigger, so if there is not a consecutive
            // scroll down event soon, the pull down trigger will be cancelled.
            startDroppingPulldownTrigger();
        } else {
            // If it is not scrolling down, immediately cancel the current pull down detection
            cancelPulldownTriggerCall();
            setPulldownProgress(0);
        }
    }, [hasElementScrolledToBottom, markPulldownTriggerEnabled,
        isPullDownTriggerCallInitiated, cancelPulldownTriggerCall, startPullDownTriggerCall, 
        startDroppingPulldownTrigger, cancelDroppingPulldownTrigger, cancelPulldownTriggerEnabled,
        pullDownTriggerEnabled, setPullDownTriggerEnabled]);

    const onScrollRefWrapper = useRef(onScroll);

    useEffect(() => {
        onScrollRefWrapper.current = onScroll;
    }, [onScrollRefWrapper, onScroll]);

    const onScrollEventListener = useCallback((event: Event) => {
        onScrollRefWrapper.current?.(event);
    }, []);

    useEffect(() => {
        const attachedDomElement = refElement.current;

        SCROLL_EVENTS.forEach(eventName => {
            attachedDomElement?.addEventListener(eventName, onScrollEventListener, {passive: true});
        });

        return () => {
            SCROLL_EVENTS.forEach(eventName => {
                attachedDomElement?.removeEventListener(eventName, onScrollEventListener);
            });
        };
    }, [refElement, onScrollEventListener]);

    return {pullDownProgress, pullDownTriggerEnabled};
}

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
        scrollToBottom
    }
}
