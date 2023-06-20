import { useMemo } from "react";
import { RowMetadataType } from "src/pages/PipelineList/common";

interface SuccessRateColumnProps {
    metadata: RowMetadataType | undefined;
}

function SuccessRateColumn(props: SuccessRateColumnProps) {
    const { metadata } = props;

    return <>{useMemo(() => {
        if (!metadata || !metadata.metrics) {
            return;
        }
        return metadata.metrics.successRate;
    }, [metadata])}</>;
}

export default SuccessRateColumn;