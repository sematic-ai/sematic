import { Check } from "@mui/icons-material";
import React, { useMemo } from "react";

interface StateChipBaseProps {
    size: "small" | "medium" | "large";
}

const useStylesHook = (props: StateChipBaseProps) => {
    const { size } = props;

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
    const styles = useStylesHook({ size: "small" });
    return <Check color={"success"} style={styles} />;
}
