import TabContext from "@mui/lab/TabContext";
import TabList from "@mui/lab/TabList";
import TabPanel from "@mui/lab/TabPanel";
import Box from "@mui/material/Box";
import Tab from "@mui/material/Tab";
import { styled } from '@mui/system';
import { Artifact } from "@sematic/common/src/Models";
import { useContext } from "react";
import { EnvContext } from "src";
import GrafanaPanel from "src/addons/grafana/GrafanaPanel";
import SourceCode from "src/components/SourceCode";
import { usePipelinePanelsContext } from "src/hooks/pipelineHooks";
import { ArtifactList } from "src/pipelines/Artifacts";
import ExternalResourcePanel from "src/pipelines/external_resource/ExternalResource";
import PodLifecycle from "src/pipelines/pod_lifecycle/PodLifecycle";
import LogPanel from "src/pipelines/LogPanel";
import OutputPanel from "src/pipelines/OutputPanel";

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
            <Tab label="Source" value="source" />
            <Tab label="Logs" value="logs" />
            {grafanaTab}
            <Tab label="Resources" value="ext_res" />
            <Tab label="Pods" value="pod_lifecycle" />
          </TabList>
        </StickyHeader>
        <TabPanel value="input">
          <ArtifactList artifacts={artifacts.input} />
        </TabPanel>
        <TabPanel value="output" sx={{ pt: 5 }}>
          <OutputPanel outputArtifacts={artifacts.output} />
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
        <TabPanel hidden={selectedRunTab !== "pod_lifecycle"} value="pod_lifecycle">
            <PodLifecycle />
        </TabPanel>
      </TabContext>
    </>
  );
}
