import styled from "@emotion/styled";
import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid";
import Link from "@mui/material/Link";
import { SimplePaletteColorOptions } from "@mui/material/styles";
import useTheme from "@mui/material/styles/useTheme";
import { useContext, useRef, useEffect } from "react";
import MuiRouterLink from "src/component/MuiRouterLink";
import NameTag from "src/component/NameTag";
import UserMenu from "src/component/UserMenu";
import UserContext from "src/context/UserContext";
import Fox from "src/static/fox";
import palette from "src/theme/new/palette";
import useLatest from "react-use/lib/useLatest";
import useCounter from "react-use/lib/useCounter";

const StyledGridContainer = styled(Grid)`
    border-bottom: 1px solid ${() => (palette.p3border as SimplePaletteColorOptions).main};
    flex-wrap: nowrap;
`;

interface HeaderMenuProps {
    selectedKey?: string;
}

const HeaderMenu = (props: HeaderMenuProps) => {
    const { selectedKey } = props;
    const theme = useTheme();

    const { user } = useContext(UserContext);
    const contextMenuAnchor = useRef(null);
    const [renderTimes, {inc}] = useCounter();

    const latestAnchor = useLatest(contextMenuAnchor.current);

    useEffect(() => {
        // re-render until the context menu anchor is set
        if (latestAnchor.current === null) {
            inc();
        }
    }, [renderTimes, inc, latestAnchor]);

    return <StyledGridContainer container spacing={0}>
        <Box style={{ flexGrow: 1, display: "flex" }} >
            <Link variant={"logo"} style={{ marginRight: theme.spacing(6) }}>
                <Fox style={{ width: "16px" }} />
            </Link>

            <MuiRouterLink variant="subtitle1" type='menu' href={"/runs"}
                className={selectedKey === "runs" ? "selected" : ""}>
                Runs
            </MuiRouterLink>
            <MuiRouterLink variant="subtitle1" type='menu' href={"/pipelines"}
                className={selectedKey === "pipelines" ? "selected" : ""}>
                Pipelines
            </MuiRouterLink>
            {/* <Link variant="subtitle1" type='menu' className={selectedKey === "metrics" ? "selected" : ""}>Metrics</Link> */}
        </Box>
        <Box style={{ flexGrow: 1, display: "flex", justifyContent: "end" }} >
            <MuiRouterLink variant="subtitle1" type='menu' href={"/"}
                className={selectedKey === "gettingstarted" ? "selected" : ""}>
                Get Started
            </MuiRouterLink>
            <Link variant="subtitle1" type='menu'>Docs</Link>
            <Link variant="subtitle1" type='menu'>Support</Link>
            <Link variant="subtitle1" type='menu'>
                <NameTag firstName={user?.first_name} lastName={user?.last_name} variant={"inherit"} 
                    ref={contextMenuAnchor} />
            </Link>
            <UserMenu anchorEl={contextMenuAnchor.current} />
        </Box>
    </StyledGridContainer>;
};

export default HeaderMenu;