import { useMemo } from "react";
import { atomWithHash } from 'jotai-location'
import { useLocation } from "react-router-dom";

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
  const { search } = useLocation();

  const isLoggingExplicitlyTurnedOn = useMemo(
    () => (new URLSearchParams(search)).has('debug'), [search]);

  const devLogger = useMemo(
    () => {
      if (process.env.NODE_ENV === "development" || isLoggingExplicitlyTurnedOn) {
        return (...args: any[]) => {
          console.log(
            `${(new Date()).toString().replace(/\sGMT.+$/, '')}  DEV DEBUG: `,
            ...args
          );
        }
      }
      return () => { };
    }, [isLoggingExplicitlyTurnedOn]);

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

export const spacing = (val: number) => ({theme}: any) => theme.spacing(val);

export async function sha1(text: string) {
  const utf8 = new TextEncoder().encode(text);
  const hashBuffer = await crypto.subtle.digest('SHA-1', utf8);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray
    .map((bytes) => bytes.toString(16).padStart(2, '0'))
    .join('');
  return hashHex;
}
