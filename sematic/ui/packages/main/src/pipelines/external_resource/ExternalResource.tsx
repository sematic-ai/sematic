import ExternalResourcePanelComponent from "@sematic/common/src/pages/RunDetails/externalResource/ExternalResource";
import { useState } from "react";
import { usePipelinePanelsContext } from "src/hooks/pipelineHooks";
import { useRunPanelLoadingIndicator } from "src/hooks/runDetailsHooks";

export default function ExternalResourcePanel() {

    const { selectedRun } = usePipelinePanelsContext();

    const [isLoading, setIsLoading] = useState<boolean>(false);

    useRunPanelLoadingIndicator(isLoading);

    if (!selectedRun) {
        return null;
    }

    return <ExternalResourcePanelComponent selectedRun={selectedRun} setIsLoading={setIsLoading}/>;
}
