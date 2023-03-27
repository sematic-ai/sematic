import Link from "@mui/material/Link";
import { ThemeProvider } from "@mui/material/styles";
import Fox from '@sematic/common/src/static/fox';
import theme from '@sematic/common/src/theme/new';
import { Meta, StoryObj } from '@storybook/react';

// More on default export: https://storybook.js.org/docs/react/writing-stories/introduction#default-export
export default {
  title: 'Sematic/Link',
  component: Link,
  decorators: [
    (Story) => (
      <ThemeProvider theme={theme}>
        <Story />
      </ThemeProvider>
    ),
  ],
} as Meta<typeof Link>;


export const LogoLink: StoryObj<typeof Link> = {
  render: () => {
    return <Link variant="logo" >
          <Fox style={{}}/>
      </Link>  
  }
};

export const MenuLink: StoryObj<typeof Link> = {
  render: () => {
    return <Link variant="subtitle1" type="menu" >
          Menu Item
      </Link>  
  }
};

export const SelectedMenuLink: StoryObj<typeof Link> = {
  render: () => {
    return <Link variant="subtitle1" type="menu" className={"selected"} >
          Menu Item
      </Link>  
  }
};


