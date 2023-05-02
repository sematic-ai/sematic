import memoize from 'lodash/memoize';
import noop from 'lodash/noop';
import { useMemo } from "react";

const getDebugState = memoize(function getDebugState() {
    const search = window.location.search;

    let debugFlagUrlValue: boolean | null;
    const strValue = (new URLSearchParams(search)).get('debug')?.toLocaleLowerCase();
    if (strValue === 'true' || strValue === '1') {
        debugFlagUrlValue = true;
    } else if (strValue === 'false' || strValue === '0') {
        debugFlagUrlValue = false;
    } else {
        debugFlagUrlValue = null;
    };

    const debugFlagLocalStorage = window.localStorage.getItem('debug');

    // if debugFlagUrlValue is set, then set it in localStorage, so that it is memorized across page refreshes
    if (debugFlagUrlValue !== null && debugFlagLocalStorage !== debugFlagUrlValue.toString()) {
        window.localStorage.setItem('debug', debugFlagUrlValue.toString());
    }

    if (debugFlagUrlValue !== null) {
        return debugFlagUrlValue;
    }

    if (debugFlagLocalStorage !== null) {
        return debugFlagLocalStorage === 'true';
    }
    return false; // default turning debug flag off
});


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
