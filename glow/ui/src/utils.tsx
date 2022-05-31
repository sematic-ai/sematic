import io from "socket.io-client";

export function fetchJSON(
  url: string,
  callback: (payload: any) => void,
  setError?: (error: Error | undefined) => void,
  setIsLoaded?: (isLoaded: boolean) => void
) {
  setIsLoaded && setIsLoaded(false);
  setError && setError(undefined);
  fetch(url)
    .then((res) => res.json())
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

export const graphSocket = io("/graph");
