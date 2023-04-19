import { ThemeProvider } from "@mui/material/styles";
import Docstring, {DocstringProps} from '@sematic/common/src/component/Docstring';
import theme from '@sematic/common/src/theme/new';
import { Meta, StoryObj } from '@storybook/react';
import CssBaseline from '@mui/material/CssBaseline';

export default {
  title: 'Sematic/Docstring',
  component: Docstring,
  decorators: [
    (Story) => (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Story />
      </ThemeProvider>
    ),
  ],
} as Meta<StoryProps>;

interface StoryProps extends DocstringProps {
  width: keyof typeof sizeOptions;
  onChange: () => void;
}

const sizeOptions = {
  "200px (small)": 200,
  "400px (medium)": 400,
  "800px (large)": 800
}

const template: StoryObj<StoryProps> = {
  render: (props) => {
    const { width, docstring } = props;

    const widthValue = width ? sizeOptions[width] : 200;

    return <div style={{maxWidth: widthValue}}><Docstring docstring={docstring} /></div>;
  },
  argTypes: {
    width: {
      control: 'select', options: Object.keys(sizeOptions)
    },
    docstring: {
      table: {
        disable: true,
      }
    }
  }
}

export const Short : StoryObj<StoryProps> = {
  ...template,
  args: {
    docstring: "This is a short docstring",
  }
};

export const Markdown : StoryObj<StoryProps> = {
  ...template,
  args: {
    docstring: "# Function header line \n                 Some of the function description goes here. 1. This is a list item 2. This is another list item",
  }
};

export const Long : StoryObj<StoryProps> = {
  ...template,
  args: {
    docstring: "This is a long docstring.\nIt has multiple lines.\n\nIt also has a blank line in the middle.",
  }
};
