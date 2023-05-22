import { parseJSON } from "date-fns";
import { DurationShort } from "src/component/DateTime";

export enum DateFormats {
    SHORT,
    LONG,
}

export function getRunStateText(futureState: string,
    timestamps: {
        createdAt: string, resolvedAt?: string, failedAt?: string, endedAt?: string
    }, dateFormat: DateFormats = DateFormats.SHORT) {
    const { createdAt, resolvedAt, failedAt, endedAt } = timestamps;


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