import { ThemeProvider } from "@mui/material/styles";
import GitInfoComponent from '@sematic/common/src/component/GitInfo';
import theme from '@sematic/common/src/theme/new';
import { Meta, StoryObj } from '@storybook/react';
import CssBaseline from '@mui/material/CssBaseline';
import SnackBarProvider from "@sematic/common/src/context/SnackBarProvider";

export default {
  title: 'Sematic/GitInfo',
  component: GitInfoComponent,
  decorators: [
    (Story) => (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Story />
      </ThemeProvider>
    ),
  ],
} as Meta<StoryProps>;

interface StoryProps {
  ["has uncommited changes"]: boolean;
  onCopied: () => void;
}


export const GitInfo: StoryObj<StoryProps> = {
  render: (props) => {
    const { "has uncommited changes": hasUncommitedChanges,
      onCopied } = props;

    return <SnackBarProvider setSnackMessageOverride={onCopied}>
      <GitInfoComponent hasUncommittedChanges={hasUncommitedChanges} />
    </SnackBarProvider>
  },
  argTypes: {
    "has uncommited changes": { control: 'boolean' },
    onCopied: { action: 'onCopied' }
  }
};

