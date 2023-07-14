import TabPanel from "@mui/lab/TabPanel";
import Tab from "@mui/material/Tab";
import EnvContext from "@sematic/common/src/context/envContext";
import { selectedRun as selectedRunAtom } from "@sematic/common/src/pages/RunDetails/atoms";
import { Fill } from "@sematic/react-slot-fill/src";
import { useContext } from "react";

import { useAtom } from "jotai";
import GraphanaPanelImport from "./GraphanaPanel";
export const GraphanaPanel = GraphanaPanelImport;

export default function GrafanaPlugin() {
    const env: Map<string, string> = useContext(EnvContext);
    const grafanaPanelUrlSettings = env.get("GRAFANA_PANEL_URL");

    const [selectedRun] = useAtom(selectedRunAtom);

    if (!grafanaPanelUrlSettings) {
        return null;
    }

    return <>
        <Fill name="run-tabs">
            <Tab label="Grafana" value="grafana" />
        </Fill>
        <Fill name="run-tabs-panels" >
            <TabPanel value="grafana">
                {!!selectedRun && <GraphanaPanel selectedRun={selectedRun as any}
                    grafanaPanelUrlSettings={grafanaPanelUrlSettings} />}
            </TabPanel>
        </Fill>
    </>
}
