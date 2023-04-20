import { useCallback, useEffect, useRef } from "react";

/**
 * This hook is used to detect if the user is selecting text. If the user is selecting text, 
 * the hook will prevent the default behavior of the click event.
 * 
 * @returns a ref that should be attached to the element that should be monitored for text selection. 
 */
export function useTextSelection<T extends HTMLElement>() {    
    const monitorElementRef = useRef() as React.MutableRefObject<T>;

    const isSelectingText = useRef(false);

    const onMouseDown = useCallback((e: Event) => {
        isSelectingText.current = false;
    }, []);

    const onMouseUp = useCallback((e: Event) => {
        if (isSelectingText.current) {
            e.preventDefault();
        }
    }, []);

    const onClick = useCallback((e: Event) => {
        if (isSelectingText.current) {
            e.preventDefault();
            e.stopPropagation();
        }
    }, []);

    const onMouseMove: (this: HTMLElement, ev: MouseEvent) => any = useCallback((e: MouseEvent) => {
        if (e.buttons === 1) {
            isSelectingText.current = true;
        }
    }, []);

    useEffect(() => {
        const monitorElement = monitorElementRef.current;

        if (monitorElement) {
            monitorElement.addEventListener("mousedown", onMouseDown);
            monitorElement.addEventListener("mouseup", onMouseUp);
            monitorElement.addEventListener("click", onClick);
            monitorElement.addEventListener("mousemove", onMouseMove);

            return () => {
                monitorElement.removeEventListener("mousedown", onMouseDown);
                monitorElement.removeEventListener("mouseup", onMouseUp);
                monitorElement.removeEventListener("click", onClick);
                monitorElement.removeEventListener("mousemove", onMouseMove);
            };
        }
    });

    return monitorElementRef;
}
