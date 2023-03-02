import { Skeleton } from "@mui/material";
import { useContext, useEffect, useState } from "react";
import { CommonValueViewProps } from "./common";
import { base64ArrayBuffer } from "src/base64ArrayBuffer";
import { UserContext } from "src/appContext";

export default function ImageValueView(props: CommonValueViewProps) {
    const { valueSummary } = props;
    const { bytes, mime_type } = valueSummary;
  
    const { user } = useContext(UserContext);
  
    const [ imageBase64, setImageBase64 ] = useState<string | undefined>(undefined);
  
    useEffect(() => {
      const headers: HeadersInit = new Headers();
      if (user?.api_key) {
        headers.set("X-API-KEY", user.api_key);
      }
      fetch(`/api/v1/storage/blobs/${bytes.blob}/data`, {headers: headers})
      .then((response) => {
        if (!response.ok) {
          throw Error(response.statusText);
        }
          return response.arrayBuffer();
      }).then((arrayBuffer) => {
        setImageBase64(base64ArrayBuffer(arrayBuffer));
      });
    }, [bytes.blob, user?.api_key]);
  
    if (imageBase64 !== undefined) {
      return <img
        src={`data:${mime_type};base64,${imageBase64}`}
        alt="Artifact rendering"
        style={{maxWidth: "600px"}}
      />
    } else {
        return <Skeleton variant="rectangular" width={210} height={60} />
    }
  }