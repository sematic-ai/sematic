import { useRef, useEffect } from "react";
import useCounter from "react-use/lib/useCounter";

/**
 * When two separate tables are used, automatically synchronize the column widths
 * of the first row of the source table to the column widths of the first row of the 
 * target table, so their columns appear fully aligned.
 * 
 * User is responsible for ensuring that the column count of the source table is the
 * same as target, or this will become a no op.
 * @returns {
 *  sourceTableRef: React reference to assign to the `ref` prop of the source table
 *  targetTableRef: React reference to assign to the `ref` prop of the target table
 * }
 */
export function useSynchornizedTables() {
  let sourceRef = useRef<HTMLTableElement>(null);
  let targetRef = useRef<HTMLTableElement>(null);

  const observerRef = useRef<MutationObserver>();

  const [counter, {inc}] = useCounter(0);

  useEffect(() => {
    if (!targetRef.current) {
        return;
    }

    if (observerRef.current) {
        observerRef.current.disconnect();
    }

    observerRef.current = new MutationObserver((mutationList) => {
        if (mutationList.length > 0) {
            inc();
        }
    });

    observerRef.current.observe(targetRef.current!, {
        childList: true, subtree: true
    });

    return () => {
        observerRef.current?.disconnect();
    };

  }, [inc]);

  useEffect(() => {
    if (!sourceRef.current || !targetRef.current) {
      return;
    }
    const sourceTableCells = Array.from<HTMLTableCellElement>(
        sourceRef.current.querySelectorAll("tr:first-child td,th")!);
    const targetTableCells = Array.from<HTMLTableCellElement>(
        targetRef.current.querySelectorAll("tr:first-child td,th")!);

    if (targetTableCells.length !== sourceTableCells.length) {
      // no op for mismatched column count
      return;
    }
    targetTableCells.forEach((td, index) => {
      td.style.width = sourceTableCells[index].style.width;
    });

  }, [counter, sourceRef, targetRef]);

  return {
    sourceTableRef: sourceRef,
    targetTableRef: targetRef
  }
}
