import { RESET } from "jotai/utils";
import { atomWithHash } from "jotai-location";

export function updateHash(currentHash: string, hashOverrideValues: Record<string, string | Symbol>) {
    let newHashValue = currentHash.replace(/^#/, "");

    const searchParams = new URLSearchParams(newHashValue);
    for (const key of Object.keys(hashOverrideValues)) {
        const value = hashOverrideValues[key]; 
        if (value === RESET) {
            searchParams.delete(key);
        } else {
            searchParams.set(key, value as string);
        }
    }
    return searchParams.toString();
}


export function atomWithHashCustomSerialization(
    name: string, initialValue: string, 
    options: Parameters<typeof atomWithHash>[2] = {}) {
    let overridenOptions = options || {};
    // Use custom serialization function to avoid generating `"`(%22) in the hash
    overridenOptions.serialize = (value: unknown) => (value as any).toString() ;
    overridenOptions.deserialize = (value: unknown) => value as string ;

    return atomWithHash<string>(name, initialValue, options as any); 
}

/**
 * Turns the following remote formats:
 * - git@gihub.com:sematic-ai/sematic.git
 * - https://github.com/sematic-ai/sematic.git
 * into clickable links:
 * - https://github.com/sematic-ai/sematic/tree/<branch>
 * - https://github.com/sematic-ai/sematic/commit/<SHA>
 */
export function makeGithubLink(remote: string, path: string) {
    let domain = remote
        .replace(/^(git@)|(https:\/\/)/, "")
        .replace(/(\.git)$/, "")
        .replace(/:/, "/");
    return "https://" + domain + "/" + path;
}
