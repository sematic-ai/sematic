import { useCallback, useRef } from "react";

/**
 * A utility to drive the function controlled by setTimeout.
 * Does not trigger re-render.
 * 
 * @param callback Function to call.
 * @param timeout how soon to call the function.
 */
export function useSetTimeout<T extends (...args: any[]) => any>(callback: T, timeout: number, label = 0): [
    (...args: Parameters<T>) => void,
    () => void,
    () => boolean
] {
    const handle = useRef<number | undefined>(undefined);
    const isPending = useRef<boolean>(false);

    const call = useCallback((...args: Parameters<T>) => {
        isPending.current = true;
        handle.current = window.setTimeout(async () => {
            const result = await callback(...args);
            isPending.current = false;
            return result;
        }, timeout);
    }, [callback, handle, timeout, isPending]);

    const cancel = useCallback(() => {
        !!handle.current && clearTimeout(handle.current);
        handle.current = undefined;
        isPending.current = false;
    }, [handle, isPending]);

    const isPendingFn = useCallback(() => isPending.current, [isPending]);

    return [call, cancel, isPendingFn];
}
