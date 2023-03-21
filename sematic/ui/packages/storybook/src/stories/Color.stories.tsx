import React from 'react';
import { ComponentStory, ComponentMeta } from '@storybook/react';
import theme from "@sematic/common/src/theme/new";
import { ThemeProvider, useTheme,  } from "@mui/material/styles";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";

import styled from "@emotion/styled";
import { Palette, PaletteColor } from "@mui/material/styles";

interface ColorBlockProps {
  paletteColorName: string;
  overrideColor?: (pallette: Palette) => { main: string, contrastText: string };
}

const StyledBlock = styled.div`
  width: 150px; 
  height: 150px;
  padding: 10px;
  line-height: 2;
`;

const ColorBlock = (props: ColorBlockProps) => {
  const { paletteColorName, overrideColor } = props;

  const theme = useTheme();
  let colorObject: Partial<PaletteColor>;

  if (overrideColor) {
    colorObject = overrideColor(theme.palette);
  } else {
    colorObject = (theme.palette as any)[paletteColorName];
  }
  const mainColor = colorObject.main;
  const contrastColor = colorObject.contrastText;

  return <StyledBlock style={{
    background: mainColor,
    color: contrastColor,
  }}>
    <Typography>{paletteColorName}</Typography>
    <Typography>{mainColor}</Typography>
  </StyledBlock>;
}


// More on default export: https://storybook.js.org/docs/react/writing-stories/introduction#default-export
export default {
  title: 'Sematic/Color',
  component: ColorBlock,

  decorators: [
    (Story) => (
      <ThemeProvider theme={theme}>
        <Story />
      </ThemeProvider>
    ),
  ],
} as ComponentMeta<typeof ColorBlock>;

// More on component templates: https://storybook.js.org/docs/react/writing-stories/introduction#using-args
const Template: ComponentStory<typeof ColorBlock> = (args) => <ColorBlock {...args} />;

export const AllColors = () => {
  const cases = [Primary, PrimaryLight, Error, Warning, Success, LightGray, Black, p3border];

  return <Grid container spacing={{ xs: 2, md: 3 }} columns={{ xs: 4, sm: 8, md: 12 }}>
    {Array.from(cases).map((c, index) => (
      <Grid item xs={2} sm={4} md={4} key={index}>
        <ColorBlock {...(c.args as any)} />
      </Grid>
    ))}
  </Grid>;
}

export const Primary = Template.bind({});
// More on args: https://storybook.js.org/docs/react/writing-stories/args
Primary.args = {
  paletteColorName: 'primary'
};

export const PrimaryLight = Template.bind({});
PrimaryLight.args = {
  paletteColorName: 'primaryLight',
  overrideColor: (palette) => {
    return {
      main: palette.primary.light,
      contrastText: palette.primary.contrastText,
    }
  }
};

export const Error = Template.bind({});
Error.args = {
  paletteColorName: 'error'
};

export const Warning = Template.bind({});
Warning.args = {
  paletteColorName: 'warning'
};

export const Success = Template.bind({});
Success.args = {
  paletteColorName: 'success'
};

export const LightGray = Template.bind({});
LightGray.args = {
  paletteColorName: 'lightGrey'
};

export const Black = Template.bind({});
Black.args = {
  paletteColorName: 'black'
};

export const p3border = Template.bind({});
p3border.args = {
  paletteColorName: 'p3border'
};
