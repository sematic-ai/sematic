import { useCallback, useEffect, useRef } from "react";
import useAsyncRetry from "react-use/lib/useAsyncRetry";
import useLatest from "react-use/lib/useLatest";
import usePreviousDistinct from "react-use/lib/usePreviousDistinct";

export function useQueuedAsyncRetry<T>(
    fn: () => Promise<T>, deps?: React.DependencyList | undefined) {
    
    const {value, loading, retry, error} = useAsyncRetry(fn, deps);

    const prevLoading = usePreviousDistinct(loading);
    const queue = useRef<Array<() => void>>([]);
    const latestRetry = useLatest(retry);

    const retryWrapped = useCallback(() => {
        if (loading) {
            queue.current = [() => {
                latestRetry.current();
            }];
        } else {
            retry();
        }
    }, [retry, latestRetry, loading, queue]);

    useEffect(() => {
        // monitors when loading changes from `true` to `false`
        if (prevLoading === true && loading === false) {
            let head = queue.current.shift()
            if (head) {
                head();
            };
        }
    }, [prevLoading, loading]);

    return {
        value, loading, error, retry: retryWrapped
    }
}