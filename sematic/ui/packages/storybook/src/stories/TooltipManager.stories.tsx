import { ThemeProvider } from "@mui/material/styles";
import ImportPathComponent from '@sematic/common/src/component/ImportPath';
import PipelineTitleComponent from '@sematic/common/src/component/PipelineTitle';
import theme from '@sematic/common/src/theme/new';
import { Meta, StoryFn } from '@storybook/react';
import CssBaseline from '@mui/material/CssBaseline';
import React from "react";

export default {
  title: 'Sematic/TooltipManager',
  component: ImportPathComponent,
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
  text: string;
  width: keyof typeof sizeOptions;
  children?: any;
}

const sizeOptions = {
  "50px (small)": 50,
  "250px (medium)": 250,
  "500px (large)": 500
}

const commonArgTypes = {
  width: {
    control: 'select', options: Object.keys(sizeOptions)
  },
  text: { control: 'text' }
};

const Template: (Component: React.FunctionComponent<any>, defaultText: string ) => StoryFn<StoryProps> 
= (Component, defaultText) => (props: StoryProps) => {
  const { text, width } = props;

  const widthValue = width ? sizeOptions[width] : 250;

  return <><div style={{ maxWidth: `${widthValue}px` }}>
    <Component >
      {text || defaultText}
    </Component>
  </div>
    <h2 style={{ position: 'absolute', bottom: "3em" }}>
      Notice: Tooltip will not show if there is enough room to display the text
    </h2>
  </>
};

export const ImportPath = Template(
  ImportPathComponent, 
  "sematic.examples.mnist.pipeline.with.very.long.path");
ImportPath.argTypes = commonArgTypes;

export const PipelineTitle = Template(
  PipelineTitleComponent,
  "Pipeline with very long name"
);
PipelineTitle.argTypes = commonArgTypes;
