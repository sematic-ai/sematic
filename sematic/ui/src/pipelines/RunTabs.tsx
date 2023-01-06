import TabContext from "@mui/lab/TabContext";
import TabList from "@mui/lab/TabList";
import TabPanel from "@mui/lab/TabPanel";
import { Alert } from "@mui/material";
import Box from "@mui/material/Box";
import Tab from "@mui/material/Tab";
import { styled } from '@mui/system';
import { useContext } from "react";
import { EnvContext } from "..";
import GrafanaPanel from "../addons/grafana/GrafanaPanel";
import { usePipelinePanelsContext} from "../hooks/pipelineHooks";
import { Artifact, Run } from "../Models";
import { ArtifactList } from "./Artifacts";
import Docstring from "../components/Docstring";
import LogPanel from "./LogPanel";
import SourceCode from "../components/SourceCode";

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
  run: Run;
  artifacts: IOArtifacts | undefined;
}) {
  const { run, artifacts } = props;

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
          {artifacts && <ArtifactList artifacts={artifacts.input} />}
        </TabPanel>
        <TabPanel value="output" sx={{ pt: 5 }}>
          {["CREATED", "SCHEDULED", "RAN"].includes(run.future_state) && (
            <Alert severity="info">No output yet. Run has not completed.</Alert>
          )}
          {["FAILED", "NESTED_FAILED"].includes(run.future_state) && (
            <Alert severity="error">Run has failed. No output.</Alert>
          )}
          {artifacts && run.future_state === "RESOLVED" && (
            <ArtifactList artifacts={artifacts.output} />
          )}
        </TabPanel>
        <TabPanel value="documentation">
          <Docstring docstring={run.description} />
        </TabPanel>
        <ExpandedTabPanel hidden={selectedRunTab !== "logs"} value="logs">
          <LogPanel run={run} />
        </ExpandedTabPanel>
        <TabPanel value="source">
          <SourceCode run={run} />
        </TabPanel>
        <TabPanel value="grafana">
          <GrafanaPanel run={run} />
        </TabPanel>
      </TabContext>
    </>
  );
}
