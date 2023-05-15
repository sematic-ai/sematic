import { parseJSON } from 'date-fns';
import { DurationShort } from 'src/component/DateTime';

export function getRunStateText(futureState: string,
    timestamps: {
        createdAt: string, resolvedAt?: string, failedAt?: string, endedAt?: string
    }) {
    const { createdAt, resolvedAt, failedAt, endedAt } = timestamps;

    if (["RESOLVED", "SUCCEEDED"].includes(futureState)) {
        return `Completed in ${DurationShort(parseJSON(resolvedAt!), parseJSON(createdAt))}`;
    }
    if (["FAILED", "NESTED_FAILED"].includes(futureState)) {
        return `Failed after ${DurationShort(parseJSON(failedAt!), parseJSON(createdAt))}`;
    }
    if (["SCHEDULED", "RAN"].includes(futureState)) {
        return `Running for ${DurationShort(new Date(), parseJSON(createdAt))}`;
    }
    if (futureState === "CANCELED") {
        const finishAt = endedAt || failedAt!;
        if (!finishAt) {
            return 'Unknonw duration';
        }
        return `Canceled after ${DurationShort(parseJSON(finishAt), parseJSON(createdAt))}`;
    }
    if (futureState === "CREATED") {
        return `Submitted ${DurationShort(new Date(), parseJSON(createdAt))} ago`;
    }
    if (futureState === "RETRYING") {
        return `Retrying for ${DurationShort(new Date(), parseJSON(createdAt))}`;
    }
    return null;
}

export default getRunStateText;