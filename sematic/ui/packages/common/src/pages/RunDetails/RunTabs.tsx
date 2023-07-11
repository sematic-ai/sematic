import styled from "@emotion/styled";
import TabContext from "@mui/lab/TabContext";
import TabList from "@mui/lab/TabList";
import TabPanel from "@mui/lab/TabPanel";
import Box from "@mui/material/Box";
import Tab from "@mui/material/Tab";
import { Slot } from "@sematic/react-slot-fill/src";
import { useAtom } from "jotai";
import { useContext } from "react";
import PluginsContext from "src/context/pluginsContext";
import { selectedTabHashAtom } from "src/hooks/runHooks";
import InputPane from "src/pages/RunDetails/artifacts/InputPane";
import OutputPane from "src/pages/RunDetails/artifacts/OutputPane";
import ExternalResourcePanel from "src/pages/RunDetails/externalResource";
import LogsPane from "src/pages/RunDetails/logs/LogsPane";
import RunMetricsPanel from "src/pages/RunDetails/metricsTab";
import PodLifecyclePanel from "src/pages/RunDetails/podLifecycle";
import SourceCodePanel from "src/pages/RunDetails/sourcecode";
import theme from "src/theme/new";

const StyledTabsContainer = styled(Box)`
    position: relative;
    margin-left: -${theme.spacing(5)};
    flex-grow: 0;
    flex-shrink: 0;

    &:after {
        content: '';
        position: absolute;
        bottom: 0;
        height: 1px;
        width: calc(100% + ${theme.spacing(5)});
        background: ${theme.palette.p3border.main};
    }
`;

const StyledTabPanel = styled(TabPanel)`
    flex-grow: 1;
    flex-shrink: 1;
    overflow-x: hidden;
    overflow-y: auto;
    padding-top: ${theme.spacing(5)};
`;

const StyledTabPanelWithoutMargin = styled(StyledTabPanel)`
    padding-top: 0;
    margin-left: -${theme.spacing(5)};
    margin-right: -${theme.spacing(5)};
`;

const ArtifactPanel = styled(StyledTabPanelWithoutMargin)`
    scrollbar-gutter: stable;
`;

const FixedTabPanel = styled(TabPanel)`
    flex-grow: 1;
    overflow: hidden;
    margin-left: -${theme.spacing(5)};
    margin-right: -${theme.spacing(5)};
`;

interface RunTabsProps {
}

const RunTabs = (props: RunTabsProps) => {
    const [selectedRunTab, setSelectedRunTab] = useAtom(selectedTabHashAtom);

    const handleChange = (event: React.SyntheticEvent, newValue: string) => {
        setSelectedRunTab(newValue);
    };

    const { RunTabs: { tabs } } = useContext(PluginsContext);

    return <TabContext value={selectedRunTab || "output"}>
        <StyledTabsContainer>
            <TabList onChange={handleChange} aria-label="Selected run tabs">
                <Tab label="Input" value="input" />
                <Tab label="Output" value="output" />
                <Tab label="Source" value="source" />
                <Tab label="Logs" value="logs" />
                <Tab label="Metrics" value="metrics" />
                <Tab label="Resources" value="ext_res" />
                <Tab label="Pods" value="pod_lifecycle" />
                {/* The below are the tabs added by plugins */}
                { tabs.map((tab, index) => <Tab key={index} label={tab} value={tab} />)}
            </TabList>
        </StyledTabsContainer>
        <ArtifactPanel value="input">
            <InputPane />
        </ArtifactPanel>
        <ArtifactPanel value="output">
            <OutputPane />
        </ArtifactPanel>
        <StyledTabPanelWithoutMargin value="source">
            <SourceCodePanel />
        </StyledTabPanelWithoutMargin>
        <FixedTabPanel value="logs">
            <LogsPane />
        </FixedTabPanel>
        <StyledTabPanel value="metrics">
            <RunMetricsPanel />
        </StyledTabPanel>
        <StyledTabPanel value="ext_res">
            <ExternalResourcePanel />
        </StyledTabPanel>
        <StyledTabPanel value="pod_lifecycle">
            <PodLifecyclePanel />
        </StyledTabPanel>
        <Slot name="run-tabs" />
    </TabContext>
};

export default RunTabs;