import { useCallback, useContext, useEffect, useMemo, useRef } from "react";
import { UserContext } from "../index";
import { useLogger } from "../utils";

interface HttpClient {
    fetch: (params: { url: string, method?: string, body?: any }) => Promise<any>;
    cancel: () => void
}

export function useHttpClient(): HttpClient {
    const { user } = useContext(UserContext);

    const headers = useMemo(() => {
        const headers: HeadersInit = new Headers();
        headers.set("Content-Type", "application/json");

        if (user?.api_key) {
            headers.set("X-API-KEY", user?.api_key);
        }

        return headers;
    }, [user?.api_key]);

    const { devLogger } = useLogger();

    const abortControllerRef = useRef<AbortController | null>(null);

    const fetchCallback = useCallback(async ({
        url,
        method,
        body
    }: { url: string, method?: string, body?: any }) => {
        method = method || "GET";

        const reqBody: BodyInit | null = body ? JSON.stringify(body) : null;

        devLogger("HttpClient.fetch ", method, url, reqBody);

        const abortController = new AbortController();
        abortControllerRef.current = (abortController);

        try{
            const response = await fetch(url, { 
                method: method, headers: headers, body: reqBody, signal: abortController.signal
            });
            abortControllerRef.current = null;
    
            if (!response.ok) {
                throw Error(response.statusText);
            }

            return response.json();
        } catch (e: any) {
            if (e instanceof DOMException && e.name === 'AbortError') {
                devLogger("fetch() was voluntarily cancelled.")
            }
            throw e;
        }

    }, [headers, devLogger]);

    const cancel = useCallback(() => {
        const abortController = abortControllerRef.current;
        if (!!abortController && !abortController.signal.aborted) {
            abortController.abort();
        }
    }, [abortControllerRef]);

    useEffect(() => {
        return ()=> {
            // Automatically cancel the request when the calling component will unmount.
            cancel();
        }
    }, [cancel]);

    return {
        fetch: fetchCallback,
        cancel
    };
}