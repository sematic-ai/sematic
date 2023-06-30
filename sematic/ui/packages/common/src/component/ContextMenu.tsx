import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import { useCallback, useEffect, useState, useMemo } from "react";

interface ContextCommand {
    title: string;
    onClick: () => void;
    disabled?: boolean;
}

interface ContextMenuProps {
    anchorEl: HTMLElement | null;
    commands: Array<ContextCommand>;
    anchorOffset?: {
        x: number;
        y: number;
    }
}

function ContextMenu(props: ContextMenuProps) {
    const { anchorEl: anchorElProp, commands, anchorOffset } = props;

    const [open, setOpen] = useState(false);
    const [anchorEl, setAnchorElement] = useState<HTMLElement>();

    const buttonClickEvent = useCallback(() => {
        setOpen((open) => !open);
    }, [setOpen]);

    useEffect(() => {
        if (anchorElProp) {
            setAnchorElement(anchorElProp);
            anchorElProp.addEventListener("click", buttonClickEvent);

            return () => {
                anchorElProp.removeEventListener("click", buttonClickEvent);
            }
        }
    }, [anchorElProp, buttonClickEvent]);

    // Use a [virtual anchor element](https://mui.com/material-ui/react-popover/#virtual-element)
    // to offset the menu
    const virtualAnchorElement = useMemo(() => ({
        nodeType: 1,
        getBoundingClientRect: () => {
            const rect = anchorEl?.getBoundingClientRect() ?? { x: 0, y: 0 };
            if (!anchorOffset) {
                return rect;
            }
            const newReact = DOMRect.fromRect(rect);
            newReact.x += anchorOffset.x;
            newReact.y += anchorOffset.y;
            return newReact;
        }
    }), [anchorEl, anchorOffset]);

    return <Menu
        anchorEl={virtualAnchorElement as any}
        open={open}
        anchorOrigin={{
            vertical: "top",
            horizontal: "right",
        }}
        transformOrigin={{
            vertical: "top",
            horizontal: "left",
        }}
        onClose={() => setOpen(false)}
    >
        {
            commands.map(({ title, disabled, onClick }, index) =>
                <MenuItem key={index} onClick={disabled ? undefined : () => {
                    setOpen(false);
                    onClick();
                }} disabled={disabled}>
                    {title}
                </MenuItem>
            )
        }
    </Menu>
}

export default ContextMenu;
