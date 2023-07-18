import styled from "@emotion/styled";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import { useContext } from "react";
import NameTag from "src/component/NameTag";
import { CommonMenu, PrivacySettingsCommand, SectionWithBorder, SwitchUICommand } from "src/component/SettingsMenu";
import UserContext from "src/context/UserContext";
import theme from "src/theme/new";

const StyledNameTag = styled(NameTag)`
    font-size: ${theme.typography.fontSize}px;
    font-weight: ${theme.typography.fontWeightBold};
    margin-bottom: ${theme.spacing(2)};
    display: inline-block;
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
    const { user, signOut } = useContext(UserContext);

    return <CommonMenu {...props}>
        <SectionWithBorder>
            <StyledNameTag firstName={user?.first_name} lastName={user?.last_name} variant={"inherit"} />
            <Typography color="GrayText">
                    API key: <code>{user?.api_key}</code>
            </Typography>
        </SectionWithBorder>
        <SwitchUICommand />
        <PrivacySettingsCommand />
        {/* Hide for now, will re-enable when we have organization support */}
        {/* <SectionWithBorder>
                <Headline>Organization</Headline>
                <Typography variant={"bold"}>Unset</Typography>
            </SectionWithBorder> */}
        <StyledButton onClick={signOut!}>Sign out</StyledButton>
    </CommonMenu >;
}

export default UserMenu;
