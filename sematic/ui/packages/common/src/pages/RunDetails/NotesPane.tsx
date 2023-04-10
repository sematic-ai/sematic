import Note, { Note as NoteType } from 'src/component/Note';
import SubmitNoteSection from 'src/pages/RunDetails/SubmitNoteSection';
import styled from '@emotion/styled';
import theme from "src/theme/new";

const MockNoteData: Array<NoteType> = [{
    name: 'Leo',
    content: 'This run looks odd, maybe we used the wrong data.',
    createdAt: '2018-01-12T12:51:51.141Z',
    runId: '8e321af4318f42cc9062451d0dd4b974',
},
{
    name: 'Michalegelo',
    content: 'I’m not sure about this. The metrics look off, and it took forever to train.',
    createdAt: '2018-01-12T12:51:51.141Z',
    runId: '8e321af4318f42cc9062451d0dd4b974',
},
{
    name: 'Einstein',
    content: 'The statement implies that the upcoming conversation is anticipated to be lengthy and will involve a significant amount of text. The speaker expresses uncertainty about the topic and whether or not it will be worthwhile to engage in this discussion. \n\nFurthermore, the speaker mentions that the metrics related to this conversation seem inaccurate or not aligned with their expectations. Additionally, they note that the process of preparing for this conversation has been arduous, requiring a considerable amount of time to prepare and train for it.',
    createdAt: '2018-01-12T12:51:51.141Z',
    runId: '8e321af4318f42cc9062451d0dd4b974',
},
{
    name: 'Einstein',
    content: 'I’m not sure about this. The metrics look off, and it took forever to train.',
    createdAt: '2018-01-12T12:51:51.141Z',
    runId: '8e321af4318f42cc9062451d0dd4b974',
}];

const Notes = styled.section`
    flex-grow: 1;
    flex-shrink: 1;
    overflow-y: auto;
    overflow-x: hidden;
    scrollbar-gutter: stable;
    margin-right: -${theme.spacing(2.4)};
`;

const NotesPane = () => {
    return <>
        <SubmitNoteSection />
        <Notes>
            {MockNoteData.map((note, index) => <Note key={index} {...note} />)}
        </Notes>
    </>;
}

export default NotesPane;
