import { GraphanaPanel } from "@sematic/addon-grafana";
import EnvContext from "@sematic/common/src/context/envContext";
import { useContext } from "react";
import { usePipelinePanelsContext } from "../../hooks/pipelineHooks";

export default function GrafanaPanel() {
    const { selectedRun } = usePipelinePanelsContext();
    const env: Map<string, string> = useContext(EnvContext);
    const grafanaPanelUrlSettings = env.get("GRAFANA_PANEL_URL");

    return <GraphanaPanel selectedRun={selectedRun!} grafanaPanelUrlSettings={grafanaPanelUrlSettings} />;
}
