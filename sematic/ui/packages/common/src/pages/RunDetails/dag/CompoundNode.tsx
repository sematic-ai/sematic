import styled from "@emotion/styled";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import IconButton from "@mui/material/IconButton";
import { useMemo } from "react";
import { NodeProps, Position } from "reactflow";
import { getRunStateChipByState, getRunStateColorByState } from "src/component/RunStateChips";
import { useHasIncoming, useNodeExpandStateToggle } from "src/hooks/dagHooks";
import { StyledHandle } from "src/pages/RunDetails/dag/common";
import theme from "src/theme/new";

const CompoundNodeContainer = styled.div`
    width: min-content;
    display: flex;
    align-items: center;
    border-width: 1px;
    border-style: solid;
    border-radius: 4px;
`;

export const LabelContainer = styled.div`
    position: absolute;
    top: 0;
    right: 0;
    left: 0;
    height: 50px;
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    font-weight: ${theme.typography.fontWeightBold};

    & svg {
        margin: 0 ${theme.spacing(2)}};
        flex-grow: 0;
    }
`;

export const StyledIconButton = styled(IconButton)`
    width: min-content;
    float: right;
    & svg {
        margin: 0;
    }
`;


function CompoundNode(props: NodeProps) {
    const { data } = props;
    const { run } = data;

    const { toggleExpanded, expanded } = useNodeExpandStateToggle(data);

    const hasIncoming = useHasIncoming();

    const stateChip = useMemo(() => getRunStateChipByState(run.future_state), [run.future_state]);
    const color = useMemo(() => getRunStateColorByState(run.future_state), [run.future_state]);
    return <CompoundNodeContainer style={{ width: `${data.width}px`, height: `${data.height}px`, borderColor: color }}>
        {hasIncoming && <StyledHandle type="target" color={color} position={Position.Top} isConnectable={false} id={"t"} />}
        <LabelContainer>
            {stateChip}
            <label style={{ flexGrow: 1 }}>{data.label}</label>
            <StyledIconButton onClick={toggleExpanded} >
                {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </StyledIconButton>
        </LabelContainer>
        <StyledHandle
            type="source"
            position={Position.Bottom}
            id="sb"
            isConnectable={false}
        />
        <StyledHandle type="target" position={Position.Bottom} isConnectable={false} id={"tb"} />
    </CompoundNodeContainer>
}

export default CompoundNode;