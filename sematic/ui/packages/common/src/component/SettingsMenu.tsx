import { css } from "@emotion/css";
import styled from "@emotion/styled";
import Link from "@mui/material/Link";
import Popover from "@mui/material/Popover";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { TrackingNoticeButton, TrackingNoticeDialogRefType } from "src/component/TrackingNotice";
import theme from "src/theme/new";

const ANCHOR_OFFSET = { x: 5, y: 0 };

const Container = styled.div`
    min-width: 300px;
    border: 1px solid ${theme.palette.p3border.main};
    border-radius: 0px 0px 3px 3px;
`;

export const SectionWithBorder = styled.section`
    padding: ${theme.spacing(5)};
    border-bottom: 1px solid ${theme.palette.p3border.main};
`;

const PaperStyleOverride = css`
    box-shadow: 0px 16px 16px -16px rgba(0, 0, 0, 0.35)!important;
`;

export function SwitchUICommand() {
    const switchToOldUI = useCallback(() => {
        window.localStorage.setItem("sematic-feature-flag-oldui", "true");
        window.location.reload();
    }, []);

    return <SectionWithBorder>
        <Link style={{ cursor: "pointer" }} onClick={switchToOldUI}>
        Switch to old UI
        </Link>
    </SectionWithBorder>
}

export function PrivacySettingsCommand() {
    const privacySettingsControl = useRef<TrackingNoticeDialogRefType>(null);

    return <SectionWithBorder>
        <TrackingNoticeButton ref={privacySettingsControl}>
            <Link style={{ cursor: "pointer" }} onClick={() => privacySettingsControl.current?.setOpen(true)}>
            Privacy Settings
            </Link>
        </TrackingNoticeButton>
    </SectionWithBorder>
};

interface CommonMenuProps {
    anchorEl: HTMLElement | null;
    children?: React.ReactNode;
}

export function CommonMenu(props: CommonMenuProps) {
    const { anchorEl: anchorElProp, children } = props;

    const [open, setOpen] = useState(false);
    const [anchorEl, setAnchorElement] = useState<HTMLElement>();

    const buttonClickEvent = useCallback(() => {
        setOpen((open) => !open);
    }, [setOpen]);

    const virtualAnchorElement = useMemo(() => ({
        nodeType: 1,
        getBoundingClientRect: () => {
            const rect = anchorEl?.getBoundingClientRect() ?? { x: 0, y: 0 };
            const newReact = DOMRect.fromRect(rect);
            newReact.x += ANCHOR_OFFSET.x;
            newReact.y += ANCHOR_OFFSET.y;
            return newReact;
        }
    }), [anchorEl]);

    useEffect(() => {
        if (anchorElProp) {
            setAnchorElement(anchorElProp);
            anchorElProp.addEventListener("click", buttonClickEvent);

            return () => {
                anchorElProp.removeEventListener("click", buttonClickEvent);
            }
        }
    }, [anchorElProp, buttonClickEvent]);

    return <Popover
        anchorEl={virtualAnchorElement as any}
        open={open}
        anchorOrigin={{
            vertical: "bottom",
            horizontal: "right",
        }}
        transformOrigin={{
            vertical: "top",
            horizontal: "right",
        }}
        onClose={() => setOpen(false)}
        PaperProps={{ className: PaperStyleOverride }}
    >
        <Container>
            {children}
        </Container>
    </Popover >;
}

function SettingsMenu(props: CommonMenuProps) {
    return <CommonMenu {...props} >
        <SwitchUICommand />
        <PrivacySettingsCommand />
    </CommonMenu>;
}

export default SettingsMenu;
