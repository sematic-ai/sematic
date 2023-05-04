import memoize from 'lodash/memoize';
import noop from 'lodash/noop';
import { useMemo } from "react";
import { getFeatureFlagValue } from 'src/utils/FeatureFlagManager';

const getDebugState = function getDebugState() {
    return getFeatureFlagValue("debug") || false; // default turning debug flag off
};

const getDevlogger = memoize(function getDevlogger() {
    const isLoggingExplicitlyTurnedOn = getDebugState();

    if (process.env.NODE_ENV === "development" || isLoggingExplicitlyTurnedOn) {
        return (...args: any[]) => {
            console.log(
                `${(new Date()).toString().replace(/\sGMT.+$/, '')}  DEV DEBUG: `,
                ...args
            );
        }
    }
    return noop;
});


export function useLogger() {
    const devLogger = useMemo(() => getDevlogger(), []);

    return {
        devLogger
    }
}
