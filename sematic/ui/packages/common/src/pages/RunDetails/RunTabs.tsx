import styled from "@emotion/styled";
import TabContext from "@mui/lab/TabContext";
import TabList from "@mui/lab/TabList";
import TabPanel from "@mui/lab/TabPanel";
import Box from "@mui/material/Box";
import Tab from "@mui/material/Tab";
import { useState } from "react";
import theme from 'src/theme/new';


const StyledTabsContainer = styled(Box)`
    position: relative;
    &:after {
        content: '';
        position: absolute;
        bottom: 0;
        height: 1px;
        width: calc(100% + ${theme.spacing(10)});
        margin-left: -${theme.spacing(5)};
        background: ${theme.palette.p3border.main};
    }
`;

interface RunTabsProps {
}

const RunTabs = (props: RunTabsProps) => {
    const [selectedRunTab, setSelectedRunTab] = useState("output");

    const handleChange = (event: React.SyntheticEvent, newValue: string) => {
        setSelectedRunTab(newValue);
    };

    return <TabContext value={selectedRunTab}>
        <StyledTabsContainer>
            <TabList onChange={handleChange} aria-label="Selected run tabs">
                <Tab label="Input" value="input" />
                <Tab label="Output" value="output" />
                <Tab label="Source" value="source" />
                <Tab label="Logs" value="logs" />
                <Tab label="Resources" value="ext_res" />
            </TabList>
        </StyledTabsContainer>
        <TabPanel value="input">
            <div />
        </TabPanel>
        <TabPanel value="output">
            <div />
        </TabPanel>
        <TabPanel value="source">
            <div />
        </TabPanel>
        <TabPanel value="logs">
            <div />
        </TabPanel>
        <TabPanel value="ext_res">
            <div />
        </TabPanel>
    </TabContext>
};

export default RunTabs;