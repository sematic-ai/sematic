import TabContext from "@mui/lab/TabContext";
import TabList from "@mui/lab/TabList";
import TabPanel from "@mui/lab/TabPanel";
import CssBaseline from '@mui/material/CssBaseline';
import Tab from "@mui/material/Tab";
import { ThemeProvider } from "@mui/material/styles";
import theme from '@sematic/common/src/theme/new';
import { Meta, StoryObj } from '@storybook/react';
import { useState } from '@sematic/common/src/reactHooks';


interface StoryProps {
  width: keyof typeof sizeOptions;
}

const sizeOptions = {
  "200px (small)": 200,
  "400px (medium)": 400,
  "800px (large)": 800
}


const ExampleComponent = () => {
  const [selectedRunTab, setSelectedRunTab] = useState("output");

  const handleChange = (event: React.SyntheticEvent, newValue: string) => {
    setSelectedRunTab(newValue);
  };

  return <TabContext value={selectedRunTab}>
    <TabList onChange={handleChange} aria-label="Selected run tabs">
      <Tab label="Input" value="input" />
      <Tab label="Output" value="output" />
      <Tab label="Source" value="source" />
      <Tab label="Logs" value="logs" />
      <Tab label="Resources" value="ext_res" />
    </TabList>
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
  </TabContext>;
}


export default {
  title: 'Sematic/Tabs',
  component: ExampleComponent,
  decorators: [
    (Story) => (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Story />
      </ThemeProvider>
    ),
  ],
} as Meta<StoryProps>;


export const Example: StoryObj<StoryProps> = {
  render: (props) => {
    const { width } = props;

    const widthValue = width ? sizeOptions[width] : 200;

    return <div style={{maxWidth: widthValue}}><ExampleComponent /></div>;
  },
  args: {
    width: "800px (large)"
  },
  argTypes: {
    width: {
      control: 'select', options: Object.keys(sizeOptions)
    }
  }
}
