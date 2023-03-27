import { ThemeProvider } from "@mui/material/styles";
import RunsDropdownComponent from '@sematic/common/src/component/RunsDropdown';
import theme from '@sematic/common/src/theme/new';
import { Meta, StoryObj } from '@storybook/react';
import CssBaseline from '@mui/material/CssBaseline';

export default {
  title: 'Sematic/Dropdown',
  component: RunsDropdownComponent,
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
  width: keyof typeof sizeOptions;
  onChange: () => void;
}

const sizeOptions = {
  "200px (small)": 200,
  "400px (medium)": 400,
  "800px (large)": 800
}

const commonArgTypes = {
  width: {
    control: 'select', options: Object.keys(sizeOptions)
  },
  onChange: { action: 'value changed' }
};

export const RunsDropdown : StoryObj<StoryProps> = {
  render: (props) => {
    const { width, onChange } = props;

    const widthValue = width ? sizeOptions[width] : 200;

    return <div style={{maxWidth: widthValue}}><RunsDropdownComponent onChange={onChange} /></div>;
  }
};
RunsDropdown.argTypes = commonArgTypes;
