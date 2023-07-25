import styled from "@emotion/styled";
import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid";
import Link from "@mui/material/Link";
import { SimplePaletteColorOptions } from "@mui/material/styles";
import useTheme from "@mui/material/styles/useTheme";
import { useContext, useRef, useEffect, useMemo } from "react";
import MuiRouterLink from "src/component/MuiRouterLink";
import NameTag from "src/component/NameTag";
import UserMenu from "src/component/UserMenu";
import UserContext from "src/context/UserContext";
import Fox from "src/static/fox";
import palette from "src/theme/new/palette";
import useLatest from "react-use/lib/useLatest";
import useCounter from "react-use/lib/useCounter";
import UserAvatar from "src/component/UserAvatar";
import { getUserInitials } from "src/utils/string";
import theme from "src/theme/new";
import SettingsMenu from "src/component/SettingsMenu";

const StyledGridContainer = styled(Grid)`
    border-bottom: 1px solid ${() => (palette.p3border as SimplePaletteColorOptions).main};
    flex-wrap: nowrap;
`;

const StyledLink = styled(Link)`
    display: flex;
    flex-direction: row;

    & > :first-of-type {
        margin-right: ${theme.spacing(1)};
    }

    &:before {
        display: none;
    }
`;

interface HeaderMenuProps {
    selectedKey?: string;
}

const HeaderMenu = (props: HeaderMenuProps) => {
    const { selectedKey } = props;
    const theme = useTheme();

    const { user } = useContext(UserContext);
    const contextMenuAnchor = useRef(null);
    const [renderTimes, { inc }] = useCounter();

    const latestAnchor = useLatest(contextMenuAnchor.current);

    const profileMenuLabel = useMemo(() => {
        if (!user) {
            return "Settings";
        }

        return <>
            <UserAvatar initials={getUserInitials(user?.first_name, user?.last_name, user?.email)} 
                hoverText={user?.first_name || user?.email} avatarUrl={user?.avatar_url} size={"medium"}/>
            <NameTag firstName={user?.first_name} lastName={undefined} variant={"inherit"} />
        </>
    }, [user]);

    const profileMenu = useMemo(() => {
        if (!user) {
            return <SettingsMenu anchorEl={contextMenuAnchor.current} />;
        }

        return <UserMenu anchorEl={contextMenuAnchor.current} />
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user, renderTimes]);

    useEffect(() => {
        // re-render until the context menu anchor is set
        if (latestAnchor.current === null) {
            inc();
        }
    }, [renderTimes, inc, latestAnchor]);

    return <StyledGridContainer container spacing={0}>
        <Box style={{ flexGrow: 1, display: "flex" }} >
            <MuiRouterLink variant={"logo"} href={"/"} style={{ marginRight: theme.spacing(6) }}>
                <Fox style={{ width: "16px" }} />
            </MuiRouterLink>

            <MuiRouterLink variant="subtitle1" type="menu" href={"/runs"}
                className={selectedKey === "runs" ? "selected" : ""}>
                Runs
            </MuiRouterLink>
            <MuiRouterLink variant="subtitle1" type="menu" href={"/pipelines"}
                className={selectedKey === "pipelines" ? "selected" : ""}>
                Pipelines
            </MuiRouterLink>
            {/* <Link variant="subtitle1" type="menu" className={selectedKey === "metrics" ? "selected" : ""}>Metrics</Link> */}
        </Box>
        <Box style={{ flexGrow: 1, display: "flex", justifyContent: "end" }} >
            <MuiRouterLink variant="subtitle1" type="menu" href={"/getstarted"}
                className={selectedKey === "gettingstarted" ? "selected" : ""}>
                Get Started
            </MuiRouterLink>
            <MuiRouterLink href={"https://docs.sematic.dev"} target={"_blank"} variant="subtitle1" type="menu">
                Docs</MuiRouterLink>
            <MuiRouterLink href={"https://discord.gg/4KZJ6kYVax"} target={"_blank"} variant="subtitle1" type="menu">
                Discord</MuiRouterLink>
            <StyledLink variant="subtitle1" type="menu" ref={contextMenuAnchor}>
                {profileMenuLabel}
            </StyledLink>
            { profileMenu }
        </Box>
    </StyledGridContainer>;
};

export default HeaderMenu;