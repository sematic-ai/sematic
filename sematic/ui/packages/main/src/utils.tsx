import { User } from "@sematic/common/src/Models";

interface IFetchJSON {
    url: string;
    callback: (payload: any) => void;
    setError?: (error: Error | undefined) => void;
    setIsLoaded?: (isLoaded: boolean) => void;
    apiKey?: string | null;
    method?: string;
    body?: any;
}

export function fetchJSON({
    url,
    callback,
    setError,
    setIsLoaded,
    apiKey,
    method,
    body,
}: IFetchJSON) {
    setIsLoaded && setIsLoaded(false);
    setError && setError(undefined);

    const headers: HeadersInit = new Headers();
    headers.set("Content-Type", "application/json");

    if (apiKey) {
        headers.set("X-API-KEY", apiKey);
    }
    headers.set(
        "X-REQUEST-ID",
        Math.floor(Math.random() * Math.pow(16, 9)).toString(16)
    );

    method = method || "GET";

    const reqBody: BodyInit | null = body ? JSON.stringify(body) : null;

    if (process.env.NODE_ENV === "development") {
        console.log("fetchJSON", method, url, reqBody);
    }

    fetch(url, { method: method, headers: headers, body: reqBody })
        .then((response) => {
            if (!response.ok) {
                throw Error(response.statusText);
            }
            return response.json();
        })
        .then(
            (payload) => {
                callback(payload);
                setIsLoaded && setIsLoaded(true);
            },
            (error) => {
                setError && setError(error);
                setIsLoaded && setIsLoaded(true);
            }
        );
}

export const spacing = (val: number) => ({theme}: any) => theme.spacing(val);

export async function sha1(text: string) {
    const utf8 = new TextEncoder().encode(text);
    const hashBuffer = await crypto.subtle.digest("SHA-1", utf8);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray
        .map((bytes) => bytes.toString(16).padStart(2, "0"))
        .join("");
    return hashHex;
}

export function abbreviatedUserName(user: User | null): string {
    if (!user) {
        return "";
    }
    const { first_name, last_name } = user;

    return `${first_name} ${(last_name || "").substring(0, 1)}.`;
}
