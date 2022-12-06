import { useCallback, useContext, useMemo } from "react";
import { UserContext } from "../index";

interface HttpClient {
    fetch: (params: { url: string, method?: string, body?: any }) => Promise<any>;
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

    return {
        fetch: useCallback(async ({
            url,
            method,
            body
        }: { url: string, method?: string, body?: any }) => {
            method = method || "GET";

            const reqBody: BodyInit | null = body ? JSON.stringify(body) : null;

            if (process.env.NODE_ENV === "development") {
                console.log("HttpClient.fetch", method, url, reqBody);
            }

            const response = await fetch(url, { method: method, headers: headers, body: reqBody });

            if (!response.ok) {
                throw Error(response.statusText);
            }

            return response.json();
        }, [headers])
    };
}