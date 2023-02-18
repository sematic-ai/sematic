import posthog from 'posthog-js';

export const optOutStorageKey = 'posthog_opt_out';

export function setupPostHogOptout() {
    let shouldUserOptout = false;

    const optOutValue = window.localStorage.getItem(optOutStorageKey);
        
    if (optOutValue === null) {
        if (!!(navigator as unknown as any)['globalPrivacyControl']) {
            shouldUserOptout = true;
        }
    } else {
        shouldUserOptout = (optOutValue === 'true');
    }

    applyPostHogOptOutSetting(shouldUserOptout);
}

export function applyPostHogOptOutSetting(shouldUserOptout: boolean) {
    if (shouldUserOptout) {
        posthog.has_opted_in_capturing() && posthog.opt_out_capturing();
    } else {
        posthog.has_opted_out_capturing() && posthog.opt_in_capturing();
    }
}
