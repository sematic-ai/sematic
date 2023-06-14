import styled from "@emotion/styled";
import TabContext from "@mui/lab/TabContext";
import TabList from "@mui/lab/TabList";
import TabPanel from "@mui/lab/TabPanel";
import Box from "@mui/material/Box";
import Tab from "@mui/material/Tab";
import { selectedTabHashAtom } from "src/hooks/runHooks";
import InputPane from "src/pages/RunDetails/artifacts/InputPane";
import OutputPane from "src/pages/RunDetails/artifacts/OutputPane";
import LogsPane from "src/pages/RunDetails/logs/LogsPane";
import theme from "src/theme/new";
import { useAtom } from "jotai";


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
    scrollbar-gutter: stable;
    margin-left: -${theme.spacing(5)};
    margin-right: -${theme.spacing(5)};
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

    return <TabContext value={selectedRunTab || "output"}>
        <StyledTabsContainer>
            <TabList onChange={handleChange} aria-label="Selected run tabs">
                <Tab label="Input" value="input" />
                <Tab label="Output" value="output" />
                <Tab label="Source" value="source" />
                <Tab label="Logs" value="logs" />
                <Tab label="Resources" value="ext_res" />
            </TabList>
        </StyledTabsContainer>
        <StyledTabPanel value="input">
            <InputPane />
        </StyledTabPanel>
        <StyledTabPanel value="output">
            <OutputPane />
        </StyledTabPanel>
        <TabPanel value="source">
            <div />
        </TabPanel>
        <FixedTabPanel value="logs">
            <LogsPane />
        </FixedTabPanel>
        <TabPanel value="ext_res">
            <div />
        </TabPanel>
    </TabContext>
};

export default RunTabs;