import BoltIcon from "@mui/icons-material/OfflineBolt";
import CheckCircle from "@mui/icons-material/CheckCircle";
import FailedIcon from "@mui/icons-material/Cancel";
import StopIcon from "@mui/icons-material/StopCircle";
import HourglassEmpty from "@mui/icons-material/HourglassEmpty";
import CheckCircleOutline from "@mui/icons-material/CheckCircleOutline";
import { useMemo } from "react";
import theme from "src/theme/new";
import { SvgIconTypeMap } from "@mui/material/SvgIcon";
import { css } from "@emotion/css";

const AnimatedChip = css`
    @keyframes svg-gaussian-blur {
        0%   {filter: url(#gaussian-blur-1); transform: scale(1.1); }
        25%  {filter: url(#gaussian-blur-0.5); }
        50%  {filter: url(#gaussian-blur-0); transform: scale(1);}
        75%  {filter: url(#gaussian-blur-0.5); }
        100%  {filter: url(#gaussian-blur-1); transform: scale(1.1);}
    }

    animation-name: svg-gaussian-blur;
    animation-duration: 1.5s;
    animation-iteration-count: infinite;
    animation-timing-function: linear;
`;

interface StateChipBaseProps {
    size?: "small" | "medium" | "large";
    animated?: boolean;
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
    return <CheckCircle color={color} style={styles} />;
}

export const FailedStateChip = (props: StateChipBaseProps) => {
    const { size } = props;
    const styles = useStylesHook({ size });
    const color = RunStateColorMap.get(FailedStateChip)!.color;
    return <FailedIcon color={color} style={styles} />;
}

export const RunningStateChip = (props: StateChipBaseProps) => {
    const { size, animated = false } = props;
    const styles = useStylesHook({ size });
    const color = RunStateColorMap.get(RunningStateChip)!.color;
    return <BoltIcon color={color} style={styles} className={animated ? AnimatedChip : undefined} />;
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
    return <CheckCircleOutline color={color} style={styles} />;
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

function getRunStateChipComponentByState(futureState: string, originalRunId: string | null) {
    if (originalRunId) {
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

export function getRunStateColorByState(futureState: string, originalRunId: string | null) {
    const Component = getRunStateChipComponentByState(futureState, originalRunId);
    if (!Component) {
        return null;
    }
    const color = RunStateColorMap.get(Component)!.color! as unknown as string
    return (theme.palette as any)[color].main;
}

interface RunStateChipProps extends StateChipBaseProps{
    futureState: string;
    originalRunId: string | null;
}

export default function RunStateChip(props: RunStateChipProps) {
    const { futureState, originalRunId, size = "large", animated } = props;

    const Component = useMemo(
        () => getRunStateChipComponentByState(futureState, originalRunId), [futureState, originalRunId]);
    if (!Component) {
        return null;
    }
    return <Component size={size} animated={animated} />;
}
