import styled from "@emotion/styled";
import { useMemo } from "react";
import { NodeProps, Position } from "reactflow";
import { getRunStateChipByState, getRunStateColorByState } from "src/component/RunStateChips";
import { useHasIncoming } from "src/hooks/dagHooks";
import { LEFT_NODE_MAX_WIDTH, StyledHandle } from "src/pages/RunDetails/dag/common";
import { SPACING } from "src/pages/RunDetails/dag/dagLayout";
import theme from "src/theme/new";

const LeftNodeContainer = styled.div`
    width: max-content;
    max-width: ${LEFT_NODE_MAX_WIDTH}px;
    height: 50px;
    display: flex;
    align-items: center;
    border: 1px solid #ccc;
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
    const { run } = data;
    const stateChip = useMemo(() => getRunStateChipByState(run.future_state), [run.future_state]);
    const color = useMemo(() => getRunStateColorByState(run.future_state), [run.future_state]);
    const hasIncoming = useHasIncoming();

    return <LeftNodeContainer style={{ paddingRight: `${SPACING}px`, borderColor: color }}>
        {hasIncoming && <StyledHandle type="target" position={Position.Top} isConnectable={false} id={"t"} />}
        <LabelContainer>
            {stateChip}
            <label >{data.label}</label>
        </LabelContainer>
        <StyledHandle
            type="source"
            position={Position.Bottom}
            id="sb"
            isConnectable={false}
        />
        <StyledHandle type="target" position={Position.Bottom} isConnectable={false} id={"tb"} />
    </LeftNodeContainer>
}

export default LeafNode;