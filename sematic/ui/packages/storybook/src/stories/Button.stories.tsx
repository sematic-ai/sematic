import Button from "@mui/material/Button";
import { ThemeProvider } from "@mui/material/styles";
import Fox from '@sematic/common/src/static/fox';
import createTheme from '@sematic/common/src/theme/new';
import { Meta, StoryObj } from '@storybook/react';

// More on default export: https://storybook.js.org/docs/react/writing-stories/introduction#default-export
export default {
  title: 'Sematic/Button',
  component: Button,
  decorators: [
    (Story) => (
      <ThemeProvider theme={createTheme()}>
        <Story />
      </ThemeProvider>
    ),
  ],
} as Meta<typeof Button>;


export const LogoButton: StoryObj<typeof Button> = {
  render: () => {
    return <Button variant="logo" >
          <Fox style={{}}/>
      </Button>  
  }
};

export const MenuButton: StoryObj<typeof Button> = {
  render: () => {
    return <Button variant="menu" >
          Menu Item
      </Button>  
  }
};


