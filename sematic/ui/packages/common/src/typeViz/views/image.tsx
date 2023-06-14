import { Skeleton, Typography } from "@mui/material";
import { useMemo } from "react";
import useFetchBlob from "src/hooks/blobHooks";
import { ArtifactExpanderContainer } from "src/typeViz/ArtifactVizTemplate";
import { ValueComponentProps, ViewComponentProps } from "src/typeViz/common";
import { base64ArrayBuffer } from "src/utils/base64ArrayBuffer";

export default function ImageValueView(props: ValueComponentProps) {
    const { open } = props;
    return open ? null : (<span>View image</span>);
}

export function ImageExpandedView(props: ViewComponentProps) {
    const { valueSummary } = props;
    const { bytes, mime_type } = valueSummary;

    const [arrayBuffer, loading, error] = useFetchBlob(bytes.blob);

    const imageBase64 = useMemo<string | undefined>(() => {
        if (arrayBuffer === undefined) return undefined;
        return base64ArrayBuffer(arrayBuffer);
    }, [arrayBuffer]);

    const glyph = useMemo(() =>  {
        if (error) {
            return <Typography>Unable to load image: {error.message}.</Typography>;
        }
    
        if (loading) {
            return <Skeleton variant="rectangular" width={210} height={60} />;
        }
    
        if (arrayBuffer) {
            return (
                <img
                    src={`data:${mime_type};base64,${imageBase64}`}
                    alt="Artifact rendering"
                    style={{ maxWidth: "900px" }}
                />
            );
        }
    
        return null

    }, [imageBase64, arrayBuffer, loading, error, mime_type]);

    return <ArtifactExpanderContainer>
        {glyph}
    </ArtifactExpanderContainer>;
} 
