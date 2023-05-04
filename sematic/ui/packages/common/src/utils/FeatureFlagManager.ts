import memoize from 'lodash/memoize';

function convertBooleanLikeValue(value: any) {
    if (value === 'true' || value === '1') {
        return true;
    } else if (value === 'false' || value === '0') {
        return false;
    } else {
        return value;
    }
}

export const getFeatureFlagValue = memoize(function getFeatureFlagValue(featureName: string) {
    const search = window.location.search;

    const strValue = (new URLSearchParams(search)).get(featureName)?.toLocaleLowerCase();
    const featureFlagUrlValue = convertBooleanLikeValue(strValue);

    const localStorageName = `sematic-feature-flag-${featureName}`;

    const localStorageValue = window.localStorage.getItem(localStorageName);

    // if featureFlagUrlValue is set, then set it in localStorage, so that it is memorized across page refreshes
    if (featureFlagUrlValue !== undefined && localStorageValue !== featureFlagUrlValue.toString()) {
        window.localStorage.setItem(localStorageName, featureFlagUrlValue.toString());
    }

    if (featureFlagUrlValue !== undefined) {
        return featureFlagUrlValue;
    }

    if (localStorageValue !== null) {
        return convertBooleanLikeValue(localStorageValue);
    }
    return undefined;
});
