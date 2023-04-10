import Chip, { chipClasses } from '@mui/material/Chip';
import Box from '@mui/material/Box';
import Button, { buttonClasses } from '@mui/material/Button';
import styled from '@emotion/styled';
import theme from 'src/theme/new';

const StyledBox = styled(Box)`
    display: flex;
    align-items: center;
    flex-wrap: wrap;

    & .${chipClasses.root}:not(*:last-of-type) {
        margin-right: ${theme.spacing(1)};
    }

    & .${buttonClasses.root} {
        margin-left: ${theme.spacing(3)};
        padding: ${theme.spacing(1)};
        height: 25px;
    }

    & > .${chipClasses.root}, & > .${buttonClasses.root}{
        margin-bottom: ${theme.spacing(1)};
    }

    // This is to offset the margin-bottom set to the last row of elements
    margin-bottom: -${theme.spacing(1)}; 
`;

interface TagsListProps {
    tags: string[];
    onClick?: (tag: string) => void;
    onAddTag?: () => void;
}

const TagsList = (props: TagsListProps) => {
    const { tags = [], onClick, onAddTag } = props;
    return <StyledBox>
        {tags.map(tag => <Chip key={tag} label={tag} onClick={() => onClick?.(tag)} />)}
        <Button variant={"text"} size={"small"} onClick={onAddTag}>add tags</Button>
    </StyledBox>;
}

export default TagsList;