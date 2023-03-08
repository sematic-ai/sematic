import { Alert, Skeleton } from "@mui/material";
import { useMemo } from "react";
import { CommonValueViewProps } from "src/types/common";
import { base64ArrayBuffer } from "src/base64ArrayBuffer";
import useFetchBlob from "src/hooks/blobHooks";

export default function ImageValueView(props: CommonValueViewProps) {
  const { valueSummary } = props;
  const { bytes, mime_type } = valueSummary;
 
  const [arrayBuffer, loading, error] = useFetchBlob(bytes.blob);

  const imageBase64 = useMemo<string | undefined>(() => {
    if (!(arrayBuffer instanceof ArrayBuffer)) return undefined;
    return base64ArrayBuffer(arrayBuffer);
  }, [arrayBuffer]);

  if (error instanceof Error || arrayBuffer instanceof Error) {
    return <Alert severity="error">Unable to load image.</Alert>
  }

  if (loading === true) {
    return <Skeleton variant="rectangular" width={210} height={60} />
  }

  if (arrayBuffer instanceof ArrayBuffer) {
    return <img
      src={`data:${mime_type};base64,${imageBase64}`}
      alt="Artifact rendering"
      style={{maxWidth: "600px"}}
    />
  }
}
