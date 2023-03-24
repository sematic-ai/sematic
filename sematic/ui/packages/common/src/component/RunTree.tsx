import styled from '@emotion/styled';
import Box from '@mui/material/Box';
import List from '@mui/material/List';
import ListItemButton, { listItemButtonClasses } from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import { SuccessStateChip } from 'src/component/RunStateChips';
import theme from 'src/theme/new';
import { Fragment } from 'react';

const StyledList = styled(List)`
    padding: 0;

    & .${listItemButtonClasses.root} {
        padding: 0;
        height: 25px;

        &.selected {
            border-right: 2px solid ${theme.palette.primary.main};
        }
    }
`;

interface ChildrenList<T> {
    value: T;
    selected?: boolean;
    children: Array<ChildrenList<T>>;
}

const RunTree = (props: {
    runTreeNodes: Array<ChildrenList<string>>;
}) => {
    const { runTreeNodes } = props;

    return <StyledList>
        {runTreeNodes.map(({ value, children, selected }, index) => (
            <Fragment key={index} >
                <ListItemButton className={selected ? 'selected': ''}>
                    <ListItemIcon sx={{ minWidth: "20px" }}>
                        <SuccessStateChip size={"small"} />
                    </ListItemIcon>
                    <ListItemText >{(value as any).toString()}</ListItemText>
                </ListItemButton>
                {
                    children.length > 0 && (
                        <Box marginLeft={1.8}>
                            <RunTree runTreeNodes={children} />
                        </Box>
                    )
                }
            </Fragment>
        ))}

    </StyledList>
}

export default RunTree;