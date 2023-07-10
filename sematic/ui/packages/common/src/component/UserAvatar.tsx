import { Avatar, AvatarProps } from "@mui/material";
import { useMemo } from "react";
import { TAG_COLORS, getTagColor } from "src/utils/color";

interface UserAvatarProps extends AvatarProps {
    avatarUrl?: string | null;
    initials?: string;
    hoverText?: string | null;
    size?: "small" | "medium" | "large";
}

const useStylesHook = (options: {
    size: NonNullable<UserAvatarProps["size"]>, 
    hasAvatar: boolean,
    initials: string | undefined
}) => {
    const { size, hasAvatar, initials } = options;

    const styles = useMemo(() => {
        const sizeMap = {
            small: {
                dimension: 15,
                fontSize: "9px",
            },
            medium: {
                dimension: 20,
                fontSize: "12px",
            },
            large: {
                dimension: 25,
                fontSize: "15px",
            }
        };
        const { dimension, fontSize } = sizeMap[size];
        if (hasAvatar) {
            return {
                width: dimension,
                height: dimension,
                fontSize,
            };
        }

        const hashInitials = initials?.split("").reduce((acc, char) => {
            return acc * 26 + (char.toLowerCase().charCodeAt(0) - "a".charCodeAt(0));
        }, 0);

        return {
            width: dimension,
            height: dimension,
            fontSize,
            ...(hashInitials ? getTagColor(hashInitials) : TAG_COLORS[5]),
        };
    }, [size, initials, hasAvatar]);

    return styles;
};

export default function UserAvatar(props: UserAvatarProps) {
    const { initials, avatarUrl, hoverText, size = "small", ...other } = props;

    const styles = useStylesHook({size, hasAvatar: !!avatarUrl, initials});

    if (!initials) {
        return null;
    }
    return (
        <Avatar
            alt={hoverText!}
            src={avatarUrl || undefined}
            sx={styles}
            {...other}
        >
            { initials }
        </Avatar >
    );
}