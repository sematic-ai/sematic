import styled from "@emotion/styled";
import { useMemo, useCallback, useContext } from "react";
import { NodeProps, Position } from "reactflow";
import { getRunStateChipByState, getRunStateColorByState } from "src/component/RunStateChips";
import { useHasIncoming } from "src/hooks/dagHooks";
import { DagViewServiceContext, LEFT_NODE_MAX_WIDTH, StyledHandleTop, StyledHandleBottom } from "src/pages/RunDetails/dag/common";
import { SPACING } from "src/pages/RunDetails/dag/dagLayout";
import theme from "src/theme/new";

const LeafNodeContainer = styled("div", {
    shouldForwardProp: (prop) => prop !== "selected"
}) <{
    selected?: boolean;
}>`
    width: max-content;
    max-width: ${LEFT_NODE_MAX_WIDTH}px;
    height: 50px;
    display: flex;
    align-items: center;
    border: ${({ selected }) => selected ? 2 : 1}px solid #ccc;
    border-radius: 4px;
`;

export const LabelContainer = styled.div`
    height: 50px;
    display: flex;
    flex-direction: row;
    align-items: center;
    font-weight: ${theme.typography.fontWeightBold};
    justify-content: flex-start;

    & svg {
        margin: 0 ${theme.spacing(2)}};
    }
`;

function LeafNode(props: NodeProps) {
    const { data } = props;
    const { run, selected } = data;
    const stateChip = useMemo(() => getRunStateChipByState(run.future_state), [run.future_state]);
    const color = useMemo(() => getRunStateColorByState(run.future_state), [run.future_state]);
    const hasIncoming = useHasIncoming();

    const { onNodeClick } = useContext(DagViewServiceContext)

    const onClick = useCallback(() => {
        onNodeClick(run.id);
    }, [onNodeClick, run]);

    return <LeafNodeContainer selected={selected} style={{ paddingRight: `${SPACING}px`, borderColor: color }}
        onClick={onClick}
    >
        {hasIncoming && <StyledHandleTop type="target" position={Position.Top} isConnectable={false} id={"t"} />}
        <LabelContainer>
            {stateChip}
            <label >{data.label}</label>
        </LabelContainer>
        <StyledHandleBottom
            type="source"
            position={Position.Bottom}
            id="sb"
            isConnectable={false}
        />
    </LeafNodeContainer>
}

export default LeafNode;