import React from 'react';
import { Meta, StoryObj } from '@storybook/react';
import Button from "@mui/material/Button";
import Fox from '@sematic/common/src/static/fox';

// More on default export: https://storybook.js.org/docs/react/writing-stories/introduction#default-export
export default {
  title: 'Sematic/Button',
  component: Button,

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


