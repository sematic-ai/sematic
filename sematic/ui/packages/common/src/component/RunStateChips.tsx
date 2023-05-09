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

export function getRunStateChipByState(futureState: string, size: StateChipBaseProps['size'] ="large") {
    if (futureState === 'SUCCESS') {
        return <SuccessStateChip size={size} />;
    }
    if (futureState === 'FAILED') {
        return <FailedStateChip size={size} />;
    }
    if (futureState === 'RUNNING') {
        return <RunningStateChip size={size} />;
    }
    if (futureState === 'CANCELLED') {
        return <CanceledStateChip size={size} />;
    }
    if (futureState === 'SCHEDULED') {
        return <SubmittedStateChip size={size} />;
    }

    return null;
}
