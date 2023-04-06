import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider } from "@mui/material/styles";
import RunTreeComponent from '@sematic/common/src/component/RunTree';
import theme from '@sematic/common/src/theme/new';
import { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { useState } from '@sematic/common/src/reactHooks';

export default {
  title: 'Sematic/Tree',
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
  runTreeNodes: keyof typeof sizeOptions;
  width: keyof typeof sizeOptions;
  onChange: (value: string) => void;
}

const sizeOptions = {
  "200px (small)": 200,
  "400px (medium)": 400,
  "800px (large)": 800
}

const commonArgTypes = {
  width: {
    control: 'select', options: Object.keys(sizeOptions)
  },
  onChange: { action: 'value changed' }
};


const RunTreeStory: React.FC<StoryProps> = (props) => {
  const [selectedValue, setSelectedValue] = useState<string>();

  const { width, onChange } = props;

  const widthValue = width ? sizeOptions[width] : 200;

  const valueExpander = (value: string) => ({
    value,
    selected: selectedValue === value
  })

  const ExampleTreeData = [
    {
      ...valueExpander('MNIST PyTorch Example'), children: [
        { ...valueExpander('Load train dataset'), children: [] as any },
        { ...valueExpander('Load test dataset'), children: [] as any },
        { ...valueExpander('get_dataloader'), children: [] as any },
        { ...valueExpander('get_dataloader_ctd'), children: [] as any },
        {
          ...valueExpander('train_eval'), children: [
            { ...valueExpander('train_model'), children: [] as any },
            { ...valueExpander('evaluate_model'), children: [] as any }
          ] as any
        },
      ] as any
    }
  ]

  return <div style={{ maxWidth: widthValue }}>
    <RunTreeComponent runTreeNodes={ExampleTreeData} onSelect={(value) => {
      onChange(value);
      setSelectedValue(value);
    }} />
  </div>;
}

export const RunTree: StoryObj<StoryProps> = {
  render: (props) => {
    return <RunTreeStory {...props} />
  },
  argTypes: commonArgTypes
};
