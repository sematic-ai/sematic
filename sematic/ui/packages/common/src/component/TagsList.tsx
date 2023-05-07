import Chip, { chipClasses } from '@mui/material/Chip';
import Box from '@mui/material/Box';
import Button, { buttonClasses } from '@mui/material/Button';
import styled from '@emotion/styled';
import theme from 'src/theme/new';
import { useMemo } from 'react';

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
    fold?: number;
    onClick?: (tag: string) => void;
    onAddTag?: () => void;
}

const TagsList = (props: TagsListProps) => {
    const { tags = [], fold, onClick, onAddTag } = props;
    const tagsToShow = useMemo(() => fold ? tags.slice(0, fold) : tags, [tags, fold]);
    const plusMore = useMemo(() => {
        if (!fold) {
            return null;
        }
        if (tags.length <= fold) {
            return null;
        }
        return <Chip label={`+${tags.length - fold}`} variant={"tag"} />
    }, [tags, fold]);

    return <StyledBox>
        {tagsToShow.map(tag => <Chip key={tag} label={tag} variant={"tag"} onClick={() => onClick?.(tag)} />)}
        {plusMore}
        {fold === undefined && <Button variant={"text"} size={"small"} onClick={onAddTag}>add tags</Button>}
    </StyledBox>;
}

export default TagsList;