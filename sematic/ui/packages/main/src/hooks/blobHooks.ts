import { useHttpClient } from "src/hooks/httpHooks";
import useAsync from "react-use/lib/useAsync";

export default function useFetchBlob(blobId: string) {
  const {fetch} = useHttpClient();

  const {value, loading, error} = useAsync(async () => {
    const response  = await fetch({
        url: `/api/v1/storage/blobs/${blobId}/data`
    });
    return ((await response.arrayBuffer()) as ArrayBuffer);
  }, [blobId]);

  return [value, loading, error];
}
