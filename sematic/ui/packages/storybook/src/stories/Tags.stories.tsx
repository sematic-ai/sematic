import CssBaseline from '@mui/material/CssBaseline';
import { ThemeProvider } from "@mui/material/styles";
import TagsListComponent from '@sematic/common/src/component/TagsList';
import TagsInputComponent from '@sematic/common/src/component/TagsInput';
import theme from '@sematic/common/src/theme/new';
import { Meta, StoryObj } from '@storybook/react';

export default {
  title: 'Sematic/Tags',
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
  width: number;
  onTagClick: (value: string) => void;
  onAddTag: () => void;
}

const commonArgTypes = {
  width: {
    name: 'Container Width',
    control: {
      type: 'range',
      min: 100,
      max: 300,
      step: 1
    }

  },
  onTagClick: { action: 'tag clicked' },
  onAddTag: { action: 'add new tag' }
};

export const TagsList: StoryObj<StoryProps> = {
  render: (props) => {
    const { width, onTagClick, onAddTag } = props;

    return <div style={{ maxWidth: width || 200 }}>
      <TagsListComponent tags={['example', 'torch', 'mnist']}
        onClick={onTagClick} onAddTag={onAddTag} />
    </div>;
  },
  argTypes: commonArgTypes
};

export const TagsInput: StoryObj<StoryProps> = {
  render: (props) => {
    const { width } = props;

    return <div style={{ maxWidth: width || 200 }}>
      <TagsInputComponent />
    </div>;
  },
  argTypes: commonArgTypes
};
