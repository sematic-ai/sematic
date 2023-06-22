import styled from "@emotion/styled";
import theme from "src/theme/new";
import Typography from "@mui/material/Typography";
import { ShellCommandRelaxed } from "src/component/ShellCommand";
import { useTheme } from "@mui/material";
import { SiDiscord, SiGithub, SiLinkedin, SiYoutube, SiTwitter } from "react-icons/si";
import { MdMenuBook } from "react-icons/md";

export const Container = styled.div`
    width: 100%;
    height: 100%;
    display: flex;

    h1 {
        margin-block-start: 0;
        margin-block-end: ${theme.spacing(5)};
    }

    p {
        margin-block-start: 0;
        margin-block-end: ${theme.spacing(5)};
        font-size: ${theme.typography.fontSize}px;
    }

    a {
        color: ${theme.palette.black.main};

        &:hover {
            color: ${theme.palette.primary.main};
        }
    }
`;

const common = `
    padding: ${theme.spacing(10)} ${theme.spacing(5)};
`

const Left = styled.div`
    width: 50%;
    border-right: 1px solid ${theme.palette.p3border.main};

    ${common}
`;

const Right = styled.div`
    width: 50%;
    overflow-y: auto;
    scrollbar-gutter: stable;

    ${common}
`;

const StyledShellCommand = styled(ShellCommandRelaxed)`
    margin-bottom: ${theme.spacing(5)};
`;

const StyledHeadline = styled.h1`
    height: 50px;
    margin-block-end: 0!important;
    display: flex;
    align-items: center;
`;

const LinkRow = styled.div`
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: flex-start;
    height: 50px;

    a {
        display: flex;
        text-decoration: none;
    }

    span {
        display: flex;
        align-items: center;
        font-weight: ${theme.typography.fontWeightBold};

        &:first-of-type {
            margin-right: ${theme.spacing(3)};
        }
    }   
`;

const GettingStarted = () => {
    const theme = useTheme();

    return (
        <Container>
            <Left>
                <h1>Set your API key</h1>
                <p>To get started, store your API key in your local settings file located at <code>~/.sematic/settings.yaml</code>.</p>
                <ShellCommandRelaxed command={"sematic settings set SEMATIC_API_KEY wyOZshRWQ1m81xml-CTWAw"}
                    style={{ marginBottom: theme.spacing(10) }} />
                <h1>Run an example pipeline</h1>
                <p>Sematic comes with a number of example pipelines ready to run.</p>
                <p>Run the MNIST example pipeline with:</p>
                <StyledShellCommand command={"sematic run examples/mnist/pytorch"} />
                <p>Or any of the following:</p>
                <Typography variant={"code"}>
                    {"・examples/mnist/pytorch"}
                    <br />
                    {"・examples/liver_cirrhosis"}
                </Typography>
                <p>Read more about examples on the <a href={"https://docs.sematic.dev/"}>Sematic Documentation</a>.</p>
            </Left>
            <Right >
                <h1>Start your own project</h1>
                <p>Start a new Sematic project from a simple template</p>
                <StyledShellCommand command={"sematic new my_new_project"} />
                <p>Or start from one of the examples:</p>
                <StyledShellCommand command={"sematic new my_new_project --from examples/mnist/pytorch"} />
                <p>Then simply run</p>
                <StyledShellCommand command={"python3 -m my_new_project"}
                    style={{ marginBottom: theme.spacing(10) }} />
                <StyledHeadline>Join the Community</StyledHeadline>
                <LinkRow>
                    <a href={"https://discord.gg/4KZJ6kYVax"}>
                        <span>
                            <SiDiscord fontSize={25} color="#4a5feb" />
                        </span>
                        <span>Join our Discord server</span>
                    </a>
                </LinkRow>
                <LinkRow>
                    <a href={"https://github.com/sematic-ai/sematic"}>
                        <span>
                            <SiGithub fontSize={25} />
                        </span>
                        <span>Star our GitHub repository</span>
                    </a>
                </LinkRow>
                <LinkRow>
                    <a href={"https://www.linkedin.com/company/sematic-ai"}>
                        <span>
                            <SiLinkedin fontSize={25} color={"#0077b7"} />
                        </span>
                        <span>Follow us on LinkedIn</span>
                    </a>
                </LinkRow>
                <LinkRow>
                    <a href={"https://www.youtube.com/@sematic-ai"}>
                        <span>
                            <SiYoutube fontSize={25} color={"#ff0000"} />
                        </span>
                        <span>Watch tutorials on our YouTube channel</span>
                    </a>
                </LinkRow>
                <LinkRow>
                    <a href={"https://twitter.com/SematicAI"}>
                        <span>
                            <SiTwitter fontSize={25} color={"#009ef7"} />
                        </span>
                        <span>Follow us on Twitter</span>
                    </a>
                </LinkRow>
                <LinkRow>
                    <a href={"https://docs.sematic.dev"}>
                        <span>
                            <MdMenuBook fontSize={25} />
                        </span>
                        <span>Read our Documentation</span>
                    </a>
                </LinkRow>

            </Right>
        </Container >
    );
};

export default GettingStarted;
