import { User } from "@sematic/common/src/Models";
import { atomWithHash } from 'jotai-location';
import memoize from 'lodash/memoize';
import noop from 'lodash/noop';
import { useMemo } from "react";

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

export const getDebugState = memoize(function getDebugState() {
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


const getDevlogger = memoize(function getDevlogger () {
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


export function abbreviatedUserName(user: User | null): string {
  if (!user) {
    return "";
  }
  const {first_name, last_name} = user;

  return `${first_name} ${(last_name || "").substring(0, 1)}.`
}


export function durationSecondsToString(durationS: number) : string {
  const displayH: number = Math.floor(durationS / 3600);
  const displayM: number = Math.floor((durationS % 3600) / 60);
  const displayS: number = Math.round(durationS % 60);

  const final = [
    displayH > 0 ? displayH.toString() + "h" : "",
    displayM > 0 ? displayM.toString() + "m " : "",
    displayS > 0 ? displayS.toString() + "s" : "",
    displayS === 0 ? "<1s" : "",
  ]
    .join(" ")
    .trim();

  return final;
}

let ID = 0;

export interface ReleaseHandle {
  (): void;
}
export class AsyncInvocationQueue {
  private queue: any[] = [];
  private instanceID: number;

  constructor() {
    this.queue = [];
    this.instanceID = ID++;
  }

  async acquire(): Promise<ReleaseHandle> {
    let resolve: any;
    const waitingPromise = new Promise((_resolve) => {
      resolve = _resolve;
    });
    this.queue.push(waitingPromise);

    // Wait until all the promises before this one have been resolved
    while (this.queue.length !== 0) {
      if (this.queue[0] === waitingPromise) { 
        break;
      }
      await this.queue.shift();
      // sleep
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
    
    // The resolve function can be used to release to the next item in the queue
    return resolve;
  }

  get InstanceID() {
    return this.instanceID;
  }

  get IsBusy() {
    return this.queue.length > 0;
  }
}
