import styled from "@emotion/styled";
import Typography from "@mui/material/Typography";
import MuiRouterLink from "src/component/MuiRouterLink";
import { ShellCommandRelaxed } from "src/component/ShellCommand";
import theme from "src/theme/new";

const InitialGuide = styled.div`
    width: 806px;
    height: 317px;
    padding: ${theme.spacing(10)};

    border: 1px solid ${theme.palette.p3border.main};
    border-radius: 5px;
`

const StyledTypography = styled(Typography)`
    margin-top: ${theme.spacing(5)};
    margin-bottom: ${theme.spacing(5)};
`

const StyledLink = styled(MuiRouterLink)`
    color: ${theme.palette.primary.main};
    font-size: ${theme.typography.big.fontSize}px;
`;

const StyledTitle = styled.h1`
    font-size: 24px;
    font-weight: 500;
    & a {
        font-size: 24px;
        font-weight: 500;
    }
`


export const NoRunNoFilters = () => <InitialGuide >
    <h1 style={{ marginTop: 0 }}>Get started with Sematic</h1>
    <StyledTypography variant={"big"}>
        Read how to <StyledLink href="/get_started">Get Started</StyledLink> or run an example pipeline.
    </StyledTypography>
    <ShellCommandRelaxed command={"sematic run examples/mnist/pytorch"} />
    <StyledTypography variant={"big"}>
        Get in touch on the <StyledLink
            href="https://discord.gg/4KZJ6kYVax"
            underline="none"
            target="_blank"
        >Sematic Discord server.</StyledLink>
    </StyledTypography>
</InitialGuide>

export const NoRunWithFilters = () => <StyledTitle>No runs found.</StyledTitle>
