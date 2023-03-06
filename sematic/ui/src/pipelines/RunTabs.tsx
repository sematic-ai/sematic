import TabContext from "@mui/lab/TabContext";
import TabList from "@mui/lab/TabList";
import TabPanel from "@mui/lab/TabPanel";
import Box from "@mui/material/Box";
import Tab from "@mui/material/Tab";
import { styled } from '@mui/system';
import { useContext } from "react";
import { EnvContext } from "..";
import GrafanaPanel from "../addons/grafana/GrafanaPanel";
import { usePipelinePanelsContext} from "../hooks/pipelineHooks";
import { Artifact } from "../Models";
import { ArtifactList } from "./Artifacts";
import LogPanel from "./LogPanel";
import SourceCode from "../components/SourceCode";
import OutputPanel from "./OutputPanel";
import ExternalResourcePanel from "./external_resource/ExternalResource";
import RunMetricsPanel from "./RunMetricsPanel";

const StickyHeader = styled(Box)`
  position: sticky;
  top: 70px;
  background: white;
  z-index: 200;
`;


export type IOArtifacts = {
  input: Map<string, Artifact | undefined>;
  output: Map<string, Artifact | undefined>;
};

export default function RunTabs(props: {
  artifacts: IOArtifacts;
}) {
  const { artifacts } = props;

  const {selectedRunTab, setSelectedRunTab, setSelectedArtifactName} = usePipelinePanelsContext();
  const handleChange = (event: React.SyntheticEvent, newValue: string) => {
    setSelectedArtifactName("");
    setSelectedRunTab(newValue);
  };

  const env: Map<string, string> = useContext(EnvContext);
  const grafanaPanelUrlSettings = env.get("GRAFANA_PANEL_URL");
  const grafanaTab = grafanaPanelUrlSettings ? (
    <Tab label="Grafana" value="grafana" />
  ) : null;

  return (
    <>
      <TabContext value={selectedRunTab}>
        <StickyHeader sx={{ borderBottom: 1, borderColor: "divider", flexShrink: 1 }}>
          <TabList onChange={handleChange} aria-label="Selected run tabs">
            <Tab label="Input" value="input" />
            <Tab label="Output" value="output" />
            <Tab label="Metrics" value="metrics" />
            <Tab label="Source" value="source" />
            <Tab label="Logs" value="logs" />
            {grafanaTab}
            <Tab label="Resources" value="ext_res" />
          </TabList>
        </StickyHeader>
        <TabPanel value="input">
          <ArtifactList artifacts={artifacts.input} />
        </TabPanel>
        <TabPanel value="output" sx={{ pt: 5 }}>
          <OutputPanel outputArtifacts={artifacts.output} />
        </TabPanel>
        <TabPanel value="metrics">
          <RunMetricsPanel />
        </TabPanel>
        <TabPanel hidden={selectedRunTab !== "logs"} value="logs">
          <LogPanel />
        </TabPanel>
        <TabPanel value="source">
          <SourceCode />
        </TabPanel>
        <TabPanel value="grafana">
          <GrafanaPanel />
        </TabPanel>
        <TabPanel hidden={selectedRunTab !== "ext_res"} value="ext_res">
            <ExternalResourcePanel />
        </TabPanel>
      </TabContext>
    </>
  );
}
