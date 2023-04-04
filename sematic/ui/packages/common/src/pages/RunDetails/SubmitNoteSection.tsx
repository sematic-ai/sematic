import styled from '@emotion/styled';

import TextField from '@mui/material/TextField';
import HeadlineBase from 'src/component/Headline';
import Section from 'src/component/Section';
import theme from 'src/theme/new';
import { useCallback, useState } from 'react';

const Headline = styled(HeadlineBase)`
    margin-bottom: ${theme.spacing(2)};
`;

const StyledSection = styled(Section)`
    display: flex;
    flex-shrink: 0;
    flex-direction: column;
    margin-bottom: 0;
    min-height: 100px;
    height: max-content;
    position: relative;

    &:after {
        content: '';
        height: 1px;
        background: ${theme.palette.p3border.main};
        width: calc(100% + ${theme.spacing(4.8)});
        position: absolute;
        bottom: 0;
        margin-left: -${theme.spacing(2.4)};
    }
}
`

interface SubmitNoteSectionProps {
    onSubmit?: (content: string) => void;
    clearTextOnSubmit?: boolean;
}

const SubmitNoteSection = (props: SubmitNoteSectionProps) => {
    const { onSubmit = console.log, clearTextOnSubmit = true } = props;
    const [composedNote, setComposedNote] = useState<string>('');

    const onSubmitCallback = useCallback(() => {
        onSubmit(composedNote);
        if (clearTextOnSubmit) {
            setComposedNote('');
        }
    }, [onSubmit, setComposedNote, composedNote, clearTextOnSubmit]);

    const onKeyDown = useCallback((e: React.KeyboardEvent<HTMLDivElement>) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            onSubmitCallback();
        }
    }, [onSubmitCallback]);

    const onChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
        setComposedNote(e.target.value)
    }, [setComposedNote]);


    return <StyledSection>
        <Headline>Notes</Headline>
        <TextField variant="standard" fullWidth multiline minRows={3} maxRows={12}
            onKeyDown={onKeyDown} placeholder="Write pipeline note..." onChange={onChange} value={composedNote}  />
    </StyledSection>;
}

export default SubmitNoteSection;
