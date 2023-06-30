import { Run } from "@sematic/common/src/Models";
import BasicMetricsPanelComponent from "@sematic/common/src/pages/RunDetails/pipelineMetrics/BasicMetricsPanel";
import { useState } from "react";
import { usePipelineRunContext } from "src/hooks/pipelineHooks";
import { useRunPanelLoadingIndicator } from "src/hooks/runDetailsHooks";

export default function BasicMetricsPanel() {
    const { rootRun } = usePipelineRunContext() as { rootRun: Run };

    const [isLoading, setIsLoading] = useState<boolean>(false);

    useRunPanelLoadingIndicator(isLoading);

    return <BasicMetricsPanelComponent runId={rootRun.id} functionPath={rootRun.function_path}
        setIsLoading={setIsLoading} />
}
