import BoltIcon from "@mui/icons-material/Bolt";
import Check from "@mui/icons-material/Check";
import ClearIcon from "@mui/icons-material/Clear";
import StopIcon from "@mui/icons-material/Stop";
import HourglassEmpty from "@mui/icons-material/HourglassEmpty";
import DoneOutline from "@mui/icons-material/DoneOutline";
import { useMemo } from "react";
import theme from "src/theme/new";
import { SvgIconTypeMap } from "@mui/material/SvgIcon";
interface StateChipBaseProps {
    size?: "small" | "medium" | "large";
}

const useStylesHook = (props: StateChipBaseProps) => {
    const { size = "small" } = props;

    const styles = useMemo(() => {
        const sizeMap = {
            small: 11,
            medium: 15,
            large: 20
        };
        const sizeValue = sizeMap[size];
        return {
            width: sizeValue,
            height: sizeValue,
        };
    }, [size]);

    return styles;
};



export const SuccessStateChip = (props: StateChipBaseProps) => {
    const { size } = props;
    const styles = useStylesHook({ size });
    const color = RunStateColorMap.get(SuccessStateChip)!.color;
    return <Check color={color} style={styles} />;
}

export const FailedStateChip = (props: StateChipBaseProps) => {
    const { size } = props;
    const styles = useStylesHook({ size });
    const color = RunStateColorMap.get(FailedStateChip)!.color;
    return <ClearIcon color={color} style={styles} />;
}

export const RunningStateChip = (props: StateChipBaseProps) => {
    const { size } = props;
    const styles = useStylesHook({ size });
    const color = RunStateColorMap.get(RunningStateChip)!.color;
    return <BoltIcon color={color} style={styles} />;
}

export const CanceledStateChip = (props: StateChipBaseProps) => {
    const { size } = props;
    const styles = useStylesHook({ size });
    const color = RunStateColorMap.get(CanceledStateChip)!.color;
    return <StopIcon color={color} style={styles} />;
}

export const SubmittedStateChip = (props: StateChipBaseProps) => {
    const { size } = props;
    const styles = useStylesHook({ size });
    const color = RunStateColorMap.get(SubmittedStateChip)!.color;
    return <HourglassEmpty color={color} style={styles} />;
}

export const CachedStateChip = (props: StateChipBaseProps) => {
    const { size } = props;
    const styles = useStylesHook({ size });
    const color = RunStateColorMap.get(CachedStateChip)!.color;
    return <DoneOutline color={color} style={styles} />;
}

const RunStateColorMap: Map<React.FC<StateChipBaseProps>, {
    color: SvgIconTypeMap<{}>["props"]["color"];
}> = new Map([
    [SuccessStateChip, { color: "success" }],
    [FailedStateChip, { color: "error" }],
    [RunningStateChip, { color: "primary" }],
    [CanceledStateChip, { color: "error" }],
    [SubmittedStateChip, { color: "lightGrey" }],
    [CachedStateChip, { color: "success" }],
]);

function getRunStateChipComponentByState(futureState: string, orignalRunId: string | null) {
    if (orignalRunId) {
        return CachedStateChip;
    }
    if (["RESOLVED", "SUCCEEDED"].includes(futureState)) {
        return SuccessStateChip;
    }
    if (["FAILED", "NESTED_FAILED"].includes(futureState)) {
        return FailedStateChip;
    }
    if (["SCHEDULED", "RAN"].includes(futureState)) {
        return RunningStateChip;
    }
    if (futureState === "CANCELED") {
        return CanceledStateChip;
    }
    if (futureState === "CREATED") {
        return SubmittedStateChip;
    }
    if (futureState === "RETRYING") {
        return RunningStateChip;
    }

    return null;
}

export function getRunStateColorByState(futureState: string, orignalRunId: string | null) {
    const Component = getRunStateChipComponentByState(futureState, orignalRunId);
    if (!Component) {
        return null;
    }
    const color = RunStateColorMap.get(Component)!.color! as unknown as string
    return (theme.palette as any)[color].main;
}

interface RunStateChipProps {
    futureState: string;
    orignalRunId: string | null;
    size?: StateChipBaseProps["size"];
}

export default function RunStateChip(props: RunStateChipProps) {
    const { futureState, orignalRunId, size = "large" } = props;

    const Component = useMemo(
        () => getRunStateChipComponentByState(futureState, orignalRunId), [futureState, orignalRunId]);
    if (!Component) {
        return null;
    }
    return <Component size={size} />;
}
