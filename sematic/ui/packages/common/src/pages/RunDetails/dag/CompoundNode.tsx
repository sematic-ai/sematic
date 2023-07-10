import styled from "@emotion/styled";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import IconButton from "@mui/material/IconButton";
import { useCallback, useContext, useMemo } from "react";
import { NodeProps, Position } from "reactflow";
import { getRunStateChipByState, getRunStateColorByState } from "src/component/RunStateChips";
import { useHasIncoming, useNodeExpandStateToggle } from "src/hooks/dagHooks";
import { DagViewServiceContext, StyledHandleBottom, StyledHandleTop } from "src/pages/RunDetails/dag/common";
import theme from "src/theme/new";
import includes from "lodash/includes";

const CompoundNodeContainer = styled("div", {
    shouldForwardProp: (prop) => !includes(["selected", "color"], prop)
}) <{
    selected?: boolean;
    color: string;
}>`
    width: min-content;
    display: flex;
    align-items: center;
    border-width: ${({ selected }) => selected ? 2 : 1}px;
    border-style: solid;
    border-radius: 4px;
    border-color: ${({ color }) => color};
    cursor: pointer;

    label {
        cursor: pointer;
    }
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
    const { run, selected } = data;

    const { toggleExpanded, expanded } = useNodeExpandStateToggle(data);

    const hasIncoming = useHasIncoming();

    const stateChip = useMemo(() => getRunStateChipByState(run.future_state), [run.future_state]);
    const color = useMemo(() => getRunStateColorByState(run.future_state), [run.future_state]);

    const { onNodeClick } = useContext(DagViewServiceContext)

    const onClick = useCallback(() => {
        onNodeClick(run.id);
    }, [onNodeClick, run]);

    return <CompoundNodeContainer selected={selected} onClick={onClick} color={color}
        style={{ width: `${data.width}px`, height: `${data.height}px` }}>
        {hasIncoming && <StyledHandleTop type="target" color={color} position={Position.Top} isConnectable={false} id={"t"} />}
        <LabelContainer>
            {stateChip}
            <label style={{ flexGrow: 1 }}>{data.label}</label>
            <StyledIconButton onClick={toggleExpanded} >
                {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </StyledIconButton>
        </LabelContainer>
        <StyledHandleBottom
            type="source"
            position={Position.Bottom}
            id="sb"
            isConnectable={false} color={color} 
        />
        <StyledHandleBottom type="target" position={Position.Bottom} isConnectable={false} id={"tb"} color={color} />
    </CompoundNodeContainer>
}

export default CompoundNode;