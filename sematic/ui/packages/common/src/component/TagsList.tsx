import Chip, { chipClasses } from '@mui/material/Chip';
import Box from '@mui/material/Box';
import Button, { buttonClasses } from '@mui/material/Button';
import styled from '@emotion/styled';
import theme from 'src/theme/new';

const StyledBox = styled(Box)`
    display: flex;
    align-items: center;

    & .${chipClasses.root}:not(*:first-of-type) {
        margin-left: ${theme.spacing(1)};
    }

    & .${buttonClasses.root} {
        margin-left: ${theme.spacing(3)};
        padding: ${theme.spacing(1)};
        height: 25px;
    }
`;

interface TagsListProps {
    tags: string[];
}

const TagsList = (props: TagsListProps) => {
    const { tags = [] } = props;
    return <StyledBox>
        {tags.map(tag => <Chip key={tag} label={tag} />)}
        <Button variant={"text"}>add tags</Button>
    </StyledBox>;
}

export default TagsList;