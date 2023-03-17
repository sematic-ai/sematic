import React from 'react';
import { ComponentStory, ComponentMeta } from '@storybook/react';
import createTheme from "@sematic/common/src/theme/new";
import { ThemeProvider, useTheme } from "@mui/material/styles";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";

import styled from "@emotion/styled";

interface ColorBlockProps {
  paletteColorName: string;
}

const StyledBlock = styled.div`
  width: 100px; 
  height: 100px;
  padding: 10px;
  line-height: 2;
`;

const ColorBlock = (props: ColorBlockProps) => {
  const { paletteColorName } = props;

  const theme = useTheme();
  const colorObject = theme.palette[paletteColorName];

  return <StyledBlock style={{
    background: colorObject.main,
    color: colorObject.contrastText,
  }}>
    <Typography>{paletteColorName}</Typography>
    <Typography>{colorObject.main}</Typography>
  </StyledBlock>;
}

// More on default export: https://storybook.js.org/docs/react/writing-stories/introduction#default-export
export default {
  title: 'Sematic/Color',
  component: ColorBlock,

  decorators: [
    (Story) => (
      <ThemeProvider theme={createTheme()}>
        <Story />
      </ThemeProvider>
    ),
  ],
} as ComponentMeta<typeof ColorBlock>;

// More on component templates: https://storybook.js.org/docs/react/writing-stories/introduction#using-args
const Template: ComponentStory<typeof ColorBlock> = (args) => <ColorBlock {...args} />;
// More on argTypes: https://storybook.js.org/docs/react/api/argtypes
const CommonArgTypes = {
  paletteColorName: {
    control: 'select', 
    options: [
      'primary', 'blue', 'error', 'warning', 'success', 'lightGray', 'black', 'p3border'
    ]
  }
};
export const AllColors = () => {
  const cases = [Primary, Blue, Error, Warning, Success, LightGray, Black, p3border];

  return <Grid container spacing={{ xs: 2, md: 3 }} columns={{ xs: 4, sm: 8, md: 12 }}>
    {Array.from(cases).map((c, index) => (
      <Grid item xs={2} sm={4} md={4} key={index}>
        <ColorBlock {...c.args} />
      </Grid>
    ))}
  </Grid>;
}

export const Primary = Template.bind({});
// More on args: https://storybook.js.org/docs/react/writing-stories/args
Primary.argTypes = CommonArgTypes;
Primary.args = {
  paletteColorName: 'primary',
};

export const Blue = Template.bind({});
Blue.argTypes = CommonArgTypes;
Blue.args = {
  paletteColorName: 'blue',
};

export const Error = Template.bind({});
Error.argTypes = CommonArgTypes;
Error.args = {
  paletteColorName: 'error',
};

export const Warning = Template.bind({});
Warning.argTypes = CommonArgTypes;
Warning.args = {
  paletteColorName: 'warning',
};

export const Success = Template.bind({});
Success.argTypes = CommonArgTypes;
Success.args = {
  paletteColorName: 'success',
};

export const LightGray = Template.bind({});
LightGray.argTypes = CommonArgTypes;
LightGray.args = {
  paletteColorName: 'lightGrey',
};

export const Black = Template.bind({});
Black.argTypes = CommonArgTypes;
Black.args = {
  paletteColorName: 'black',
};

export const p3border = Template.bind({});
p3border.argTypes = CommonArgTypes;
p3border.args = {
  paletteColorName: 'p3border',
};
