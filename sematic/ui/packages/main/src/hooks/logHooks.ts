import { useHttpClient } from "@sematic/common/src/hooks/httpHooks";
import { useRefFn } from "@sematic/common/src/utils/hooks";
import { useLogger } from "@sematic/common/src/utils/logging";
import { useCallback, useRef, useState } from "react";
import useAsyncFn from "react-use/lib/useAsyncFn";
import useList from "react-use/lib/useList";
import { LogLineRequestResponse } from "../Payloads";

const MAX_LINES = 2000;
export interface GetNextResult {
    pulledLines?: number;
    canceled?: boolean;
}

export enum DiagnosticReasons {
    BOOTSTRAP = "BOOTSTRAP",
    BOOTSTRAP_REV = "BOOTSTRAP-REVERSE",
    PREV = "PREV",
    NEXT = "NEXT"
}

/**
 * This function is used to prune the lines that are already in the Set.
 */
function pruneLines(currentlineIds: Set<number>, newLines: string[], newLineIds: number[]) {
    if (newLines.length !== newLineIds.length) {
        throw new Error('Received lines and lineIds are not of the same length.');
    }

    const linesToAdded: string[] = [];

    for (let i = 0; i < newLines.length; i++) {
        const newLineId = newLineIds[i];
        const newLine = newLines[i];

        if (!currentlineIds.has(newLineId)) {
            linesToAdded.push(newLine);
            currentlineIds.add(newLineId);
        }
    }

    return linesToAdded;
}

export function useLogStream(source: string, filterString: string) {
    const { fetch } = useHttpClient();
    const { devLogger } = useLogger();

    const FetchOccurenceCounters = useRef({
        [DiagnosticReasons.BOOTSTRAP]: 0,
        [DiagnosticReasons.BOOTSTRAP_REV]: 0,
        [DiagnosticReasons.NEXT]: 0,
        [DiagnosticReasons.PREV]: 0
    });

    const [lines, { set: setLines, push: pushLines }] = useList<string>([]);
    const [logInfoMessage, setlogInfoMessage] = useState<string | null>(null);
    const [canContinueBackward, setCanContinueBackward] = useState<boolean>(false);
    const [canContinueForward, setCanContinueForward] = useState<boolean>(false);

    const lineIds = useRefFn<Set<number>>(() => new Set());
    const forwardCursorToken = useRef<string | null>();
    const reverseCursorToken = useRef<string | null>();
    const prependLines = useCallback((newLines: Array<string>, newLineIds: Array<number>) => {
        const linesToAdded = pruneLines(lineIds, newLines, newLineIds);
        setLines((lines) => linesToAdded.concat(lines));
    }, [lineIds, setLines]);

    const appendLines = useCallback((newLines: Array<string>, newLineIds: Array<number>) => {
        const linesToAdded = pruneLines(lineIds, newLines, newLineIds);
        pushLines(...linesToAdded);
    }, [lineIds, pushLines]);

    const [{ loading: isLoading, error }, fetchCommon] = useAsyncFn(
        async (reason: DiagnosticReasons, _queryParams: Record<string, string>) => {
            FetchOccurenceCounters.current[reason] += 1;
            const occurenceID = FetchOccurenceCounters.current[reason];
            const DEBUG_TAG = `${reason}_${occurenceID}`;

            devLogger(`logHooks.ts [${DEBUG_TAG}] kickoff() started. filter_string: ${filterString}`);

            let queryParams: any = {
                'DEBUG': DEBUG_TAG,
                max_lines: '' + MAX_LINES,
                ..._queryParams
            };

            if (!!filterString) {
                queryParams['filter_string'] = filterString;
            }

            const qString = (new URLSearchParams(queryParams)).toString();
            const url = `/api/v1/runs/${source}/logs?${qString}`;

            const payload: LogLineRequestResponse = await (await fetch({ url })).json();

            const { content: { lines, line_ids, log_info_message, can_continue_backward,
                can_continue_forward, forward_cursor_token, reverse_cursor_token } } = payload;

            devLogger(`logHooks.ts [${DEBUG_TAG}] getNext() ${url} completed. `
                + `# of lines: ${(!!lines ? lines.length : NaN)} `
                + `forward_cursor_token: ${forward_cursor_token && atob(forward_cursor_token)} `
                + `reverse_cursor_token: ${reverse_cursor_token && atob(reverse_cursor_token)} `);

            setlogInfoMessage(log_info_message);

            return {
                lines, lineIds: line_ids, forward_cursor_token, reverse_cursor_token,
                can_continue_backward, can_continue_forward
            };
        }, []);

    const kickOff = useCallback(async (reverse: boolean) => {
        const reason = reverse ? DiagnosticReasons.BOOTSTRAP_REV : DiagnosticReasons.BOOTSTRAP;

        let queryParams: any = {
        };

        if (!!reverse) {
            queryParams['reverse'] = 'true';
        }

        const result = await fetchCommon(reason, queryParams);
        if (result instanceof Error) {
            return;
        }

        const { lines: newlines, lineIds: newLineIds, forward_cursor_token, reverse_cursor_token,
            can_continue_backward, can_continue_forward } = result;

        setLines(newlines);
        lineIds.clear();
        newLineIds.forEach((id) => lineIds.add(id));

        setCanContinueBackward(can_continue_backward);
        setCanContinueForward(can_continue_forward);

        forwardCursorToken.current = forward_cursor_token;
        reverseCursorToken.current = reverse_cursor_token;
    }, [fetchCommon, setLines, lineIds]);

    const fetchBeginning = useCallback(async () => {
        await kickOff(false);
    }, [kickOff]);

    const fetchEnd = useCallback(async () => {
        await kickOff(true);
    }, [kickOff]);

    const getNext = useCallback(async () => {
        let queryParams: any = {
            forward_cursor_token: forwardCursorToken.current
        };
        const result = await fetchCommon(DiagnosticReasons.NEXT, queryParams);
        if (result instanceof Error) {
            return;
        }
        const { lines: newlines, lineIds: newLineIds, forward_cursor_token, can_continue_forward }
            = result;

        forwardCursorToken.current = forward_cursor_token;
        appendLines(newlines, newLineIds);
        setCanContinueForward(can_continue_forward);
    }, [fetchCommon, appendLines]);

    const getPrev = useCallback(async () => {
        let queryParams: any = {
            reverse_cursor_token: reverseCursorToken.current,
            reverse: 'true'
        };
        const result = await fetchCommon(DiagnosticReasons.PREV, queryParams);
        if (result instanceof Error) {
            return;
        }
        const { lines: newlines, lineIds: newLineIds, reverse_cursor_token, can_continue_backward }
            = result;

        reverseCursorToken.current = reverse_cursor_token;
        prependLines(newlines, newLineIds);
        setCanContinueBackward(can_continue_backward);
    }, [fetchCommon, prependLines]);

    return {
        lines, isLoading, error, logInfoMessage, canContinueBackward, canContinueForward,
        fetchBeginning, fetchEnd, getNext, getPrev
    };
}
