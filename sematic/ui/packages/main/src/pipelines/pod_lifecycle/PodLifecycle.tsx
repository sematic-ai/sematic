import PodLifecycleComponent from "@sematic/common/src/pages/RunDetails/podLifecycle/PodLifecycle";
import { usePipelinePanelsContext } from "src/hooks/pipelineHooks";
import { useRunPanelLoadingIndicator } from "src/hooks/runDetailsHooks";
import { useState } from "react";


export default function PodLifecycle() {
    const { selectedRun } = usePipelinePanelsContext();

    const [isLoading, setIsLoading] = useState<boolean>(false);

    useRunPanelLoadingIndicator(isLoading);

    return <PodLifecycleComponent key={selectedRun!.id} runId={selectedRun!.id} setIsLoading={setIsLoading}/>
}
