import MetricsPane from "@sematic/common/src/pages/RunDetails/metricsTab/MetricsPane";
import { useState } from "react";
import { usePipelinePanelsContext } from "src/hooks/pipelineHooks";
import { useRunPanelLoadingIndicator } from "src/hooks/runDetailsHooks";

export default function RunMetricsPanel() {
    const { selectedRun } = usePipelinePanelsContext();

    const [isLoading, setIsLoading] = useState<boolean>(false);

    useRunPanelLoadingIndicator(isLoading);

    let run = selectedRun!;
    return <MetricsPane run={run} setIsLoading={setIsLoading} />;
}
