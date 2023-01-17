import { useMemo } from "react";
import io from "socket.io-client";
import { atomWithHash } from 'jotai-location'

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


export function atomWithHashCustomSerialization(
  name: string, initialValue: string, 
  options: Parameters<typeof atomWithHash>[2] = {}) {
  let overridenOptions = options || {};
  // Use custom serialization function to avoid generating `"`(%22) in the hash
  overridenOptions.serialize = (value: unknown) => (value as any).toString() ;
  overridenOptions.deserialize = (value: unknown) => value as string ;

  return atomWithHash<string>(name, initialValue, options as any); 
}

export const graphSocket = io("/graph");

export const pipelineSocket = io("/pipeline");
