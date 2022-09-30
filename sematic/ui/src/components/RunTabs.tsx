import Box from "@mui/material/Box";
import { useState, useContext } from "react";
import { Artifact, Edge, Run } from "../Models";
import { ArtifactList } from "./Artifacts";
import SourceCode from "./SourceCode";
import Tab from "@mui/material/Tab";
import TabContext from "@mui/lab/TabContext";
import TabList from "@mui/lab/TabList";
import TabPanel from "@mui/lab/TabPanel";
import Docstring from "./Docstring";
import { Alert } from "@mui/material";
import LogPanel from "./LogPanel";
import GrafanaPanel from "../addons/grafana/GrafanaPanel";
import { EnvContext } from "../";

export type IOArtifacts = {
  input: Map<string, Artifact | undefined>;
  output: Map<string, Artifact | undefined>;
};

type Graph = {
  runs: Map<string, Run>;
  edges: Edge[];
  artifacts: Artifact[];
};

export default function RunTabs(props: {
  run: Run;
  artifacts: IOArtifacts | undefined;
}) {
  const { run, artifacts } = props;

  const defaultTab = run.future_state === "FAILED" ? "logs" : "output";

  const [selectedTab, setSelectedTab] = useState(defaultTab);

  const handleChange = (event: React.SyntheticEvent, newValue: string) => {
    setSelectedTab(newValue);
  };

  const env: Map<string, string> = useContext(EnvContext);
  const grafanaPanelUrlSettings = env.get("GRAFANA_PANEL_URL");
  const grafanaTab = grafanaPanelUrlSettings ? (
    <Tab label="Grafana" value="grafana" />
  ) : (
    <></>
  );

  return (
    <>
      <TabContext value={selectedTab}>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
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
            <Alert severity="info">No output yet. Run has not completed</Alert>
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
        <TabPanel value="logs">
          <LogPanel run={run} />
        </TabPanel>
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
