import { parseJSON } from 'date-fns';
import { DurationShort } from 'src/component/DateTime';

export function getRunStateText(futureState: string,
    timestamps: { createdAt: string, resolvedAt?: string, failedAt?: string, canceledAt?: string }) {
    const { createdAt, resolvedAt, failedAt, canceledAt } = timestamps;

    if (futureState === 'SUCCESS') {
        return `Completed in ${DurationShort(parseJSON(resolvedAt!), parseJSON(createdAt))}`;
    }
    if (futureState === 'FAILED') {
        return `Failed after ${DurationShort(parseJSON(failedAt!), parseJSON(createdAt))}`;
    }
    if (futureState === 'RUNNING') {
        return `Running for ${DurationShort(new Date(), parseJSON(createdAt))}`;
    }
    if (futureState === 'CANCELLED') {
        return `Canceled after ${DurationShort(parseJSON(canceledAt!), parseJSON(createdAt))}`;
    }
    if (futureState === 'SCHEDULED') {
        return 'Submitted';
    }
    return null;
}

export default getRunStateText;