import { ThemeProvider } from "@mui/material/styles";
import Menu from '@sematic/common/src/component/menu';
import createTheme from '@sematic/common/src/theme/new';
import { Meta, StoryObj } from '@storybook/react';

export default {
  title: 'Sematic/Header',
  component: Menu,
  decorators: [
    (Story) => (
      <ThemeProvider theme={createTheme()}>
        <Story />
      </ThemeProvider>
    ),
  ],
} as Meta<typeof Menu>;


export const Header: StoryObj<typeof Menu> = {
  render: () => {
    return <Menu />
  }
};

