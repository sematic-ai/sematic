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
import DocumentationPanel from "./DocumentationPanel";
import OutputPanel from "./OutputPanel";

const ExpandedTabPanel = styled(TabPanel)<{hidden: boolean}>( 
  ({hidden}) => hidden ? {} : {
    display: 'flex',
    flexGrow: 1,
    paddingBottom: 0
  });


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
        <Box sx={{ borderBottom: 1, borderColor: "divider", flexShrink: 1 }}>
          <TabList onChange={handleChange} aria-label="Selected run tabs">
            <Tab label="Input" value="input" />
            <Tab label="Output" value="output" />
            <Tab label="Source" value="source" />
            <Tab label="Logs" value="logs" />
            {grafanaTab}
          </TabList>
        </Box>
        <TabPanel value="input">
          <ArtifactList artifacts={artifacts.input} />
        </TabPanel>
        <TabPanel value="output" sx={{ pt: 5 }}>
          <OutputPanel outputArtifacts={artifacts.output} />
        </TabPanel>
        <TabPanel value="documentation">
          <DocumentationPanel />
        </TabPanel>
        <ExpandedTabPanel hidden={selectedRunTab !== "logs"} value="logs">
          <LogPanel />
        </ExpandedTabPanel>
        <TabPanel value="source">
          <SourceCode />
        </TabPanel>
        <TabPanel value="grafana">
          <GrafanaPanel />
        </TabPanel>
      </TabContext>
    </>
  );
}
