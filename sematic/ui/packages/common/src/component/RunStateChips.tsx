import BoltIcon from "@mui/icons-material/Bolt";
import Check from "@mui/icons-material/Check";
import ClearIcon from "@mui/icons-material/Clear";
import StopIcon from "@mui/icons-material/Stop";
import ArrowUpward from "@mui/icons-material/ArrowUpward";
import { useMemo } from "react";
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
    return <Check color={"success"} style={styles} />;
}

export const FailedStateChip = (props: StateChipBaseProps) => {
    const { size } = props;
    const styles = useStylesHook({ size });
    return <ClearIcon color={"error"} style={styles} />;
}

export const RunningStateChip = (props: StateChipBaseProps) => {
    const { size } = props;
    const styles = useStylesHook({ size });
    return <BoltIcon color={"primary"} style={styles} />;
}

export const CanceledStateChip = (props: StateChipBaseProps) => {
    const { size } = props;
    const styles = useStylesHook({ size });
    return <StopIcon color={"error"} style={styles} />;
}

export const SubmittedStateChip = (props: StateChipBaseProps) => {
    const { size } = props;
    const styles = useStylesHook({ size });
    return <ArrowUpward color={"lightGrey"} style={styles} />;
}

export function getRunStateChipByState(futureState: string, size: StateChipBaseProps['size'] = "large") {
    if (["RESOLVED", "SUCCEEDED"].includes(futureState)) {
        return <SuccessStateChip size={size} />;
    }
    if (["FAILED", "NESTED_FAILED"].includes(futureState)) {
        return <FailedStateChip size={size} />;
    }
    if (["SCHEDULED", "RAN"].includes(futureState)) {
        return <RunningStateChip size={size} />;
    }
    if (futureState === "CANCELED") {
        return <CanceledStateChip size={size} />;
    }
    if (futureState === "CREATED") {
        return <SubmittedStateChip size={size} />;
    }
    if (futureState === "RETRYING") {
        return <RunningStateChip size={size} />;
    }

    return null;
}
