import styled from "@emotion/styled";
import Box from "@mui/material/Box";
import List from "@mui/material/List";
import ListItemButton, { listItemButtonClasses } from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import { Fragment } from "react";
import { getRunStateChipByState } from "src/component/RunStateChips";
import { RunTreeNode } from "src/interfaces/graph";
import theme from "src/theme/new";
import range from "lodash/range";
import Skeleton from "@mui/material/Skeleton";
import { Run } from "src/Models";

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

const StyledSkeleton = styled(Skeleton)`
    width: 100%;
    margin-right: ${theme.spacing(5)};
`;

interface RunTreeProps {
    runTreeNodes: Array<RunTreeNode>;
    onSelect?: (runId: string) => void;
    selectedRunId?: string;
}

const RunTree = (props: RunTreeProps) => {
    const { runTreeNodes, onSelect, selectedRunId } = props;

    return <StyledList>
        {(runTreeNodes as Array<RunTreeNode & {run: Run}>).map(({ run, children }, index) => (
            <Fragment key={`${index}---${run.id}`} >
                <ListItemButton className={selectedRunId === run.id ? "selected" : ""}
                    onClick={() => onSelect?.(run.id)}>
                    <ListItemIcon sx={{ minWidth: "20px" }}>
                        {getRunStateChipByState(run.future_state, "small")}
                    </ListItemIcon>
                    <ListItemText >{run.name}</ListItemText>
                </ListItemButton>
                {
                    children.length > 0 && (
                        <Box marginLeft={1.8}>
                            <RunTree runTreeNodes={children} onSelect={onSelect} selectedRunId={selectedRunId} />
                        </Box>
                    )
                }
            </Fragment>
        ))}
    </StyledList>
}

export const RunTreeSkeleton = () => <StyledList>
    {range(5).map((_, index) => (
        <Fragment key={index} >
            <ListItemButton>
                <StyledSkeleton />
            </ListItemButton>
        </Fragment>
    ))}
</StyledList>

export default RunTree;