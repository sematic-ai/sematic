import styled from '@emotion/styled';
import Chip from '@mui/material/Chip';
import TextField from '@mui/material/TextField';
import { useCallback, useRef, useState } from 'react';
import theme from 'src/theme/new';

interface OverflowComponentProps {
  overflow: boolean;
  isEmpty: boolean;
}

const TagsContainer = styled.div`
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    row-gap: ${theme.spacing(0.8)};
    column-gap: ${theme.spacing(0.8)};
`;

const MaskLayer = styled('div', {
  shouldForwardProp: (prop) => !["overflow", "isEmpty"].includes(prop as any),
})<OverflowComponentProps>`
  position: absolute;
  left: 0px;
  top: 0;
  right: 0px;
  bottom: 0;
  width: 100%;
  user-select: none;
  pointer-events: none;
  overflow-x: ${({ overflow }) => overflow ? 'hidden' : 'visible'};
  visibility: ${({ overflow, isEmpty }) => overflow || isEmpty ? 'hidden' : 'visible'};

  & > div {
    width: min-content;
    color: transparent;
    position: relative;

    &::after {
      content: '↵';
      position: absolute;
      left: calc(100% + 1px);
      top: 4px;
      color: ${theme.palette.lightGrey.main};
    }
  }
`;

const InputContainer = styled('div', {
  shouldForwardProp: (prop) => !["overflow", "isEmpty"].includes(prop as any),
})<OverflowComponentProps>`
  position: relative;
  width: 100%;

  &::after {
    content: '↵';
    position: absolute;
    left: 100%;
    top: 4px;
    color: ${theme.palette.lightGrey.main};
    display: ${({ overflow, isEmpty }) => overflow && !isEmpty ? 'block' : 'none'};
  }
`;

const TagsInput = () => {
  const [tags, setTags] = useState<string[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [overflow, setOverflow] = useState(false);
  const inputRef = useRef<HTMLInputElement>();
  const maskLayer = useRef<HTMLDivElement>(null);

  const syncOverflowState = useCallback(() => {
    setOverflow(inputRef.current!.clientWidth <= maskLayer.current!.clientWidth);
  }, []);

  const handleAddTag = useCallback(() => {
    if (inputValue.trim() !== '') {
      setTags([...tags, inputValue.trim()]);
      setInputValue('');
      syncOverflowState();
    }
  }, [tags, inputValue, syncOverflowState]);

  const handleRemoveTag = useCallback((tag: string) => {
    const updatedTags = tags.filter((t) => t !== tag);
    setTags(updatedTags);
  }, [tags]);

  const handleInputChange = useCallback((e: any) => {
    setInputValue(e.target.value);
  }, []);

  return (
    <>
      <TagsContainer>
        {tags.map((tag, index) => (
          <Chip key={index} label={tag} variant={'tag'} onDelete={() => handleRemoveTag(tag)} />
        ))}
      </TagsContainer>
      <InputContainer overflow={overflow} isEmpty={inputValue === ''}>
        <TextField value={inputValue} variant="standard" onChange={handleInputChange} placeholder={"Tags..."}
          inputRef={inputRef}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              handleAddTag();
            }
            syncOverflowState();
          }}
          style={{ width: '100%' }}
        />
        <MaskLayer overflow={overflow} isEmpty={inputValue === ''} >
          <div ref={maskLayer}>
            {inputValue}
          </div>
        </MaskLayer>
      </InputContainer>
    </>
  );
};

export default TagsInput;
