import { css } from "@emotion/css";
import styled from "@emotion/styled";
import Button from "@mui/material/Button";
import Popover from "@mui/material/Popover";
import Typography from "@mui/material/Typography";
import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import NameTag from "src/component/NameTag";
import UserContext from "src/context/UserContext";
import theme from "src/theme/new";

const ANCHOR_OFFSET = { x: 5, y: 15 };

const Container = styled.div`
    min-width: 300px;
    border: 1px solid ${theme.palette.p3border.main};
    border-radius: 0px 0px 3px 3px;
`;

const SectionWithBorder = styled.section`
    padding: ${theme.spacing(5)};
    border-bottom: 1px solid ${theme.palette.p3border.main};
`;

const StyledNameTag = styled(NameTag)`
    font-size: ${theme.typography.fontSize}px;
    font-weight: ${theme.typography.fontWeightBold};
    margin-bottom: ${theme.spacing(2)};
    display: inline-block;
`;

const PaperStyleOverride = css`
    box-shadow: 0px 16px 16px -16px rgba(0, 0, 0, 0.35)!important;
`;

const StyledButton = styled(Button)`
    width: 100%;
    height: 50px;
    color: ${theme.palette.error.main};
    display: flex;
    justify-content: flex-start;
    padding-left: 25px;
    font-weight: ${theme.typography.fontWeightBold};
`;

interface UserMenuProps {
    anchorEl: HTMLElement | null;
}

function UserMenu(props: UserMenuProps) {
    const { anchorEl: anchorElProp } = props;

    const [open, setOpen] = useState(false);
    const [anchorEl, setAnchorElement] = useState<HTMLElement>();

    const { user, signOut } = useContext(UserContext);

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
        if (anchorElProp && user) {
            setAnchorElement(anchorElProp);
            anchorElProp.addEventListener("click", buttonClickEvent);

            return () => {
                anchorElProp.removeEventListener("click", buttonClickEvent);
            }
        }
    }, [anchorElProp, user, buttonClickEvent]);

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
            <SectionWithBorder>
                <StyledNameTag firstName={user?.first_name} lastName={user?.last_name} variant={"inherit"} />
                <Typography color="GrayText">
                    API key: <code>{user?.api_key}</code>
                </Typography>
            </SectionWithBorder>
            {/* Hide for now, will re-enable when we have organization support */}
            {/* <SectionWithBorder>
                <Headline>Organization</Headline>
                <Typography variant={"bold"}>Unset</Typography>
            </SectionWithBorder> */}
            <StyledButton onClick={signOut!}>Sign out</StyledButton>
        </Container>
    </Popover >;
}

export default UserMenu;
