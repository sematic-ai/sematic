import { Fill } from "@sematic/react-slot-fill/src";
import TabPanel from "@mui/lab/TabPanel";
import { useContext, useEffect } from "react";
import EnvContext from "@sematic/common/src/context/envContext";
import PluginsContext from "@sematic/common/src/context/pluginsContext";
import { selectedRun as selectedRunAtom } from "@sematic/common/src/pages/RunDetails/atoms";

import GraphanaPanelImport from "./GraphanaPanel";
import { useAtom } from "jotai";
export const GraphanaPanel = GraphanaPanelImport;

export default function GrafanaPlugin() {
    const env: Map<string, string> = useContext(EnvContext);
    const grafanaPanelUrlSettings = env.get("GRAFANA_PANEL_URL");

    const { RunTabs: { addTab } } = useContext(PluginsContext);

    const [selectedRun] = useAtom(selectedRunAtom);

    useEffect(() => {
        if (!grafanaPanelUrlSettings) return;
        addTab("Grafana");
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    if (!grafanaPanelUrlSettings) {
        return null;
    }

    return <Fill name="run-tabs" >
        <TabPanel value="Grafana">
            {!!selectedRun && <GraphanaPanel selectedRun={selectedRun as any} 
                grafanaPanelUrlSettings={grafanaPanelUrlSettings}/>}
        </TabPanel>
    </Fill>
}
