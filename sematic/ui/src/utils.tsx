import { useMemo } from "react";
import io from "socket.io-client";

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

export function useLogger() {
  const devLogger = useMemo(() => process.env.NODE_ENV === "development" ?
    (...args: any[]) => console.log("DEV DEBUG: ", ...args) :
    () => { }, []);

  return {
    devLogger
  }
} 

export const graphSocket = io("/graph");

export const pipelineSocket = io("/pipeline");
