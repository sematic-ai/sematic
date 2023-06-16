import { useMemo } from "react";
import { RowMetadataType } from "src/pages/PipelineList/common";

interface AvgRuntimeColumnProps {
    metadata: RowMetadataType | undefined;
}

function AvgRuntimeColumn(props: AvgRuntimeColumnProps) {
    const { metadata } = props;

    return <>{useMemo(() => {
        if (!metadata || !metadata.metrics) {
            return;
        }
        return metadata.metrics.avgRuntime;
    }, [metadata])}</>;
}

export default AvgRuntimeColumn;