import { ThemeProvider } from "@mui/material/styles";
import NoteComponent from '@sematic/common/src/component/Note';
import theme from '@sematic/common/src/theme/new';
import { Meta, StoryFn, StoryObj } from '@storybook/react';
import CssBaseline from '@mui/material/CssBaseline';
import SubmitNoteSection from '@sematic/common/src/pages/RunDetails/SubmitNoteSection';

export default {
  title: 'Sematic/Notes',
  component: NoteComponent,
  decorators: [
    (Story) => (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Story />
      </ThemeProvider>
    ),
  ],
} as Meta<StoryProps>;

interface StoryProps extends React.ComponentProps<typeof NoteComponent> {
  example: string;
  width?: keyof (typeof sizeOptions);
  onSubmit?: (content: string) => void;
}

const Examples: Record<string, React.ComponentProps<typeof NoteComponent>> = {
  "Clean": {
    name: 'Leo',
    content: 'This run looks odd, maybe we used the wrong data.',
    createdAt: '2018-01-12T12:51:51.141Z',
    runId: '8e321af4318f42cc9062451d0dd4b974',
  },
  "Long Content": {
    name: 'Raphael',
    content: 'The statement implies that the upcoming conversation is anticipated to be lengthy and will involve a significant amount of text. The speaker expresses uncertainty about the topic and whether or not it will be worthwhile to engage in this discussion. \n\nFurthermore, the speaker mentions that the metrics related to this conversation seem inaccurate or not aligned with their expectations. Additionally, they note that the process of preparing for this conversation has been arduous, requiring a considerable amount of time to prepare and train for it.',
    createdAt: '2018-01-12T12:51:51.141Z',
    runId: '8e321af4318f42cc9062451d0dd4b974',
  },
  "Long Content & Name": {
    name: 'Donato di Niccolò di Betto Bardi',
    content: 'The statement implies that the upcoming conversation is anticipated to be lengthy and will involve a significant amount of text. The speaker expresses uncertainty about the topic and whether or not it will be worthwhile to engage in this discussion. \n\nFurthermore, the speaker mentions that the metrics related to this conversation seem inaccurate or not aligned with their expectations. Additionally, they note that the process of preparing for this conversation has been arduous, requiring a considerable amount of time to prepare and train for it.',
    createdAt: '2018-01-12T12:51:51.141Z',
    runId: '8e321af4318f42cc9062451d0dd4b974',
  },
  "Long name": {
    name: 'Michalegelo',
    content: 'I’m not sure about this. The metrics look off, and it took forever to train.',
    createdAt: '2018-01-12T12:51:51.141Z',
    runId: '8e321af4318f42cc9062451d0dd4b974',
  }
}

const Template: StoryFn<StoryProps> = (props: StoryProps) => {
  const { example = "Clean" } = props;
  const mockData = Examples[example] || Examples["clean"];
  return <div style={{ width: '300px' }}><NoteComponent {...mockData} /></div>;
};

const commonArgTypes = {
  example: {
    control: {
      type: 'select',
    },
    options: Object.keys(Examples),
  },
};

export const Note1 = Template.bind({});
Note1.args = {
  example: "Clean"
};
Note1.argTypes = commonArgTypes;

const sizeOptions = {
  "200px (small)": 200,
  "400px (medium)": 400,
  "800px (large)": 800
}


export const NoteSubmission: StoryObj<StoryProps> = {
  render: (props) => {
    const { width, onSubmit} = props;

    const keys = Object.keys(sizeOptions) as (keyof typeof sizeOptions)[];

    const widthValue = sizeOptions[width || keys[1]];

    return <div style={{width: widthValue}}>
      <SubmitNoteSection onSubmit={onSubmit!} />
    </div>
  },
  argTypes: {
    width: {
      control: 'select', options: Object.keys(sizeOptions)      
    },
    onSubmit: { action: 'value changed' }
  }
}
