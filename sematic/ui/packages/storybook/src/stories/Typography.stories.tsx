import React from 'react';
import { ComponentStory, ComponentMeta } from '@storybook/react';
import Typography from "@mui/material/Typography";
import { ThemeProvider } from "@mui/material/styles";
import theme from "@sematic/common/src/theme/new";

export default {
  title: 'Sematic/Typography',
  component: Typography,
  decorators: [
    (Story) => (
      <ThemeProvider theme={theme}>
        <Story />
      </ThemeProvider>
    ),
  ],
} as ComponentMeta<typeof Typography>;

const Template: ComponentStory<typeof Typography> = (args) => <Typography {...args} >
  The quick fox jumps over the lazy dog
</Typography>;

export const Regular = Template.bind({});
Regular.args = {};


export const Small = Template.bind({});
Small.args = {
  variant: 'small'
};

export const Big = Template.bind({});
Big.args = {
  variant: 'big'
};

export const Bold = Template.bind({});
Bold.args = {
  variant: 'bold'
};

export const BigBold = Template.bind({});
BigBold.args = {
  variant: 'bigBold'
};
