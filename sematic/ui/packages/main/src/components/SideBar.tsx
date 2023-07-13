import { Logout, PlayCircle, Timeline } from "@mui/icons-material";
import {
    Box,
    ButtonBase,
    Divider,
    IconButton,
    ListItem,
    ListItemIcon,
    Menu,
    MenuItem,
    Stack,
    Typography,
} from "@mui/material";
import Link from "@mui/material/Link";
import { useTheme } from "@mui/material/styles";
import MuiRouterLink from "@sematic/common/src/component/MuiRouterLink";
import UserContext from "@sematic/common/src/context/UserContext";
import { useCallback, useContext, useState } from "react";
import { SiDiscord, SiReadthedocs } from "react-icons/si";
import logo from "../Fox.png";
import UserAvatar from "./UserAvatar";

export default function SideBar() {
    const theme = useTheme();

    return (
        <Box
            sx={{
                display: "grid",
                gridTemplateRows: "auto 1fr auto",
                gridTemplateColumns: "auto",
                backgroundColor: theme.palette.grey[800],
                color: "rgba(255, 255, 255, 0.5)",
                textAlign: "center",
                height: "100%",
            }}
        >
            <Stack sx={{ gridRow: 1, spacing: 2, paddingTop: 3 }}>
                <Box sx={{ color: "#ffffff", paddingBottom: 4 }}>
                    <MuiRouterLink href="/" underline="none">
                        <img src={logo} width="30px" alt="Sematic fox" />
                        {/*<Typography fontSize={32}>🦊</Typography>*/}
                    </MuiRouterLink>
                </Box>
                <Box mt={5}>
                    <MuiRouterLink
                        href="/pipelines"
                        sx={{ color: "rgba(255, 255, 255, 0.5)" }}
                        underline="none"
                    >
                        <Timeline fontSize="large" />
                        <Typography fontSize={10}>Pipelines</Typography>
                    </MuiRouterLink>
                </Box>
                <Box mt={5}>
                    <MuiRouterLink
                        href="/runs"
                        sx={{ color: "rgba(255, 255, 255, 0.5)" }}
                        underline="none"
                    >
                        <PlayCircle fontSize="large" />
                        <Typography fontSize={10}>Runs</Typography>
                    </MuiRouterLink>
                </Box>
            </Stack>
            <Stack
                spacing={4}
                sx={{
                    gridRow: 3,
                    fontSize: 24,
                    paddingBottom: 4,
                }}
            >
                <Stack spacing={4} sx={{ paddingBottom: 4 }}>
                    <Box>
                        <MuiRouterLink
                            href="https://docs.sematic.dev"
                            sx={{ color: "rgba(255, 255, 255, 0.5)" }}
                            underline="none"
                            target="_blank"
                        >
                            <SiReadthedocs />
                            <Typography fontSize={10}>Docs</Typography>
                        </MuiRouterLink>
                    </Box>
                    <Box>
                        <MuiRouterLink
                            href="https://discord.gg/4KZJ6kYVax"
                            sx={{ color: "rgba(255, 255, 255, 0.5)" }}
                            underline="none"
                        >
                            <SiDiscord />
                            <Typography fontSize={10}>Discord</Typography>
                        </MuiRouterLink>
                    </Box>
                </Stack>
                <UserMenu />
            </Stack>
        </Box>
    );
}

function UserMenu() {
    const { user, signOut } = useContext(UserContext);

    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
    const open = Boolean(anchorEl);
    const handleClick = (event: React.MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
    };
    const handleClose = () => {
        setAnchorEl(null);
    };
    
    const switchToNewUI = useCallback(() => {
        window.localStorage.setItem("sematic-feature-flag-newui", "true");
        window.location.reload();
    }, []);

    return user && signOut ? (
        <>
            <Box>
                <IconButton
                    onClick={handleClick}
                    size="small"
                    aria-controls={open ? "account-menu" : undefined}
                    aria-haspopup="true"
                    aria-expanded={open ? "true" : undefined}
                >
                    <UserAvatar user={user} sx={{ mx: "auto", mb: 1 }} />
                </IconButton>
            </Box>
            <Menu
                id="account-menu"
                open={open}
                onClose={handleClose}
                PaperProps={{
                    elevation: 0,
                    sx: {
                        overflow: "visible",
                        filter: "drop-shadow(0px 2px 8px rgba(0,0,0,0.32))",
                        ml: 13,
                        mt: -1,
                        "&:before": {
                            content: '""',
                            display: "block",
                            position: "absolute",
                            bottom: 18,
                            left: 0,
                            width: 10,
                            height: 10,
                            bgcolor: "background.paper",
                            transform: "translateX(-50%) rotate(45deg)",
                            zIndex: 0,
                        },
                    },
                }}
            >
                <ListItem sx={{ pb: 0 }}>
                    <Typography variant="h6">
                        {user.first_name + " " + user.last_name}
                    </Typography>
                </ListItem>
                <ListItem sx={{ py: 2 }}>
                    <Typography color="GrayText">{user.email}</Typography>
                </ListItem>
                <ListItem sx={{ pt: 0, pb: 4 }}>
                    <Typography color="GrayText">
                        API key: <code>{user.api_key}</code>
                    </Typography>
                </ListItem>
                <Divider />
                <ListItem sx={{ height: "50px", display: "flex", alignItems: "center"}}>
                    <Typography color="GrayText">
                        <Link style={{ cursor: "pointer"}} onClick={switchToNewUI}>
                            Switch to new UI
                        </Link>
                    </Typography>
                </ListItem>
                <Divider />
                <MenuItem sx={{ mt: 2 }}>
                    <ButtonBase onClick={signOut}>
                        <ListItemIcon>
                            <Logout fontSize="small" />
                        </ListItemIcon>
                        Sign out
                    </ButtonBase>
                </MenuItem>
            </Menu>
        </>
    ) : (
        <></>
    );
}
