import { ThemeProvider } from "@mui/material/styles";
import { SuccessStateChip as SuccessStateChipComponent, 
  FailedStateChip as FailedStateChipComponent,
  RunningStateChip as RunningStateChipComponent,
  CanceledStateChip as CanceledStateChipComponent
 } from '@sematic/common/src/component/RunStateChips';
import theme from '@sematic/common/src/theme/new';
import { Meta, StoryFn } from '@storybook/react';
import CssBaseline from '@mui/material/CssBaseline';

const sizeOptions = ["small", "medium", "large"] as const;

const typeOptions = {
  "Success": SuccessStateChipComponent,
  "Failed": FailedStateChipComponent,
  "Running": RunningStateChipComponent,
  "Canceled": CanceledStateChipComponent
}

export default {
  title: 'Sematic/RunStateChip',
  decorators: [
    (Story) => (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Story />
      </ThemeProvider>
    ),
  ],
  argTypes: {
    type: {
      control: 'select', options: Object.keys(typeOptions),
    },
    size: {
      control: 'select', options: sizeOptions
    }
  }
} as Meta<StoryProps>;

interface StoryProps {
  type: keyof typeof typeOptions;
  size: (typeof sizeOptions)[number];
}

const Template: StoryFn<StoryProps> = (props: StoryProps) => {
    const { type, size = "large" } = props;
    const Component = typeOptions[type];
    return <Component size={size}/>
  };

export const SuccessStateChip = Template.bind({});
SuccessStateChip.args = {
  type: "Success",
}

export const FailedStateChip = Template.bind({});
FailedStateChip.args = {
  type: "Failed",
}

export const RunningStateChip = Template.bind({});
RunningStateChip.args = {
  type: "Running",
}

export const CanceledStateChip = Template.bind({});
CanceledStateChip.args = {
  type: "Canceled",
}
