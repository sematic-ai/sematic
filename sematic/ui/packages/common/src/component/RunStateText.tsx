import { parseJSON } from "date-fns";
import { ReactNode } from "react";
import { DurationShort } from "src/component/DateTime";
import { RunReferenceLink } from "src/component/RunReference";
import styled from "@emotion/styled";
import theme from "src/theme/new";

const StyledRunReferenceLink = styled(RunReferenceLink)`
    color: ${theme.palette.lightGrey.main};
`;


export enum DateFormats {
    SHORT,
    LONG,
}

interface GetRunStateTextOptions {
    short?: boolean;
}

export function getRunStateText(futureState: string, originalRunId: string | null,
    timestamps: {
        createdAt: string, resolvedAt?: string, failedAt?: string, endedAt?: string
    }, options: GetRunStateTextOptions = {}): ReactNode {
    const { createdAt, resolvedAt, failedAt, endedAt } = timestamps;
    const { short = false } = options;

    if (originalRunId) {
        return short ? "Cached" : <>
            {"Cached from"}
            <StyledRunReferenceLink runId={originalRunId} variant="code" />
        </>;
    }

    if (["RESOLVED", "SUCCEEDED"].includes(futureState)) {
        if (!resolvedAt) {
            return "Completed in unknown duration";
        }
        return `Completed in ${DurationShort(parseJSON(resolvedAt!), parseJSON(createdAt)) || "< 1s"}`;
    }
    if (["FAILED", "NESTED_FAILED"].includes(futureState)) {
        if (!failedAt) {
            return "Failed after unknown duration";
        }
        return `Failed after ${DurationShort(parseJSON(failedAt!), parseJSON(createdAt)) || "< 1s"}`;
    }
    if (["SCHEDULED", "RAN"].includes(futureState)) {
        return `Running for ${DurationShort(new Date(), parseJSON(createdAt)) || "< 1s"}`;
    }
    if (futureState === "CANCELED") {
        const finishAt = endedAt || failedAt!;
        if (!finishAt) {
            return "Canceled after unknown duration";
        }
        return `Canceled after ${DurationShort(parseJSON(finishAt), parseJSON(createdAt)) || "< 1s"}`;
    }
    if (futureState === "CREATED") {
        return `Submitted ${DurationShort(new Date(), parseJSON(createdAt)) || "< 1s"} ago`;
    }
    if (futureState === "RETRYING") {
        return `Retrying for ${DurationShort(new Date(), parseJSON(createdAt)) || "< 1s"}`;
    }
    return null;
}

export default getRunStateText;