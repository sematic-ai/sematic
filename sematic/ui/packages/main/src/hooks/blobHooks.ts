import { useHttpClient } from "src/hooks/httpHooks";
import useAsync from "react-use/lib/useAsync";

export default function useFetchBlob(blobId: string): [
  ArrayBuffer | undefined,
  boolean,
  Error | undefined
] {
  const {fetch} = useHttpClient();

  const {value, loading, error} = useAsync(async () => {
    const response  = await fetch({
        url: `/api/v1/storage/blobs/${blobId}/data?origin=${window.location.origin}`
    });
    return ((await response.arrayBuffer()) as ArrayBuffer);
  }, [blobId]);

  return [value, loading, error];
}
