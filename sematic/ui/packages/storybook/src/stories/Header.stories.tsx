import { ThemeProvider } from "@mui/material/styles";
import Menu from '@sematic/common/src/component/menu';
import theme from '@sematic/common/src/theme/new';
import { Meta, StoryObj } from '@storybook/react';

export default {
  title: 'Sematic/Header',
  component: Menu,
  decorators: [
    (Story) => (
      <ThemeProvider theme={theme}>
        <Story />
      </ThemeProvider>
    ),
  ],
} as Meta<StoryProps>;

interface StoryProps {
  selectedItem: string;
}


export const Header: StoryObj<StoryProps> = {
  render: (props) => {
    const { selectedItem } = props;

    return <Menu selectedKey={selectedItem}/>
  },
  argTypes: {
    selectedItem: {
      control: 'select', 
      options: [
        undefined, 'runs', 'pipelines', 'metrics'
      ]
    }
  }
};

