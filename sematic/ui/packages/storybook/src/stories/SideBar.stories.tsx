import { Meta, StoryObj } from '@storybook/react';
import MetaDataPane from "@sematic/common/src/pages/RunDetails/MetaDataPane";
import { ThemeProvider } from "@mui/material/styles";
import theme from '@sematic/common/src/theme/new';
import CssBaseline from '@mui/material/CssBaseline';

// More on default export: https://storybook.js.org/docs/react/writing-stories/introduction#default-export
export default {
  title: 'Sematic/Sidebar',
  component: MetaDataPane,
  decorators: [
    (Story) => (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Story />
      </ThemeProvider>
    ),
  ],
} as Meta<typeof MetaDataPane>;

type Story = StoryObj<typeof MetaDataPane>;

export const Sidebar: Story = {
  render: () => <MetaDataPane />,
};
