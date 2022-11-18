import { ContentCopy } from "@mui/icons-material";
import {
  Box,
  ButtonBase,
  Container,
  Divider,
  Grid,
  Link,
  Typography,
  useTheme,
} from "@mui/material";
import {
  ReactElement,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { SiDiscord, SiReadthedocs, SiGithub } from "react-icons/si";
import { UserContext } from ".";
import RunStateChip from "./components/RunStateChip";
import { RunListPayload } from "./Payloads";
import { fetchJSON } from "./utils";

function ShellCommand(props: { command: string }) {
  const { command } = props;

  const [content, setContent] = useState("$ " + command);

  const theme = useTheme();

  const onClick = useCallback(() => {
    navigator.clipboard.writeText(command);
    setContent("Copied!");
    setTimeout(() => setContent("$ " + command), 1000);
  }, [command]);

  return (
    <ButtonBase
      sx={{
        backgroundColor: theme.palette.grey[800],
        color: theme.palette.grey[100],
        py: 1,
        px: 2,
        borderRadius: 1,
        display: "flex",
        width: "100%",
        textAlign: "left",
        boxShadow: "rgba(0,0,0,0.5) 0px 0px 5px 0px",
      }}
      onClick={onClick}
    >
      <code style={{ flexGrow: 1 }}>{content}</code>
      <ContentCopy fontSize="small" sx={{ color: theme.palette.grey[600] }} />
    </ButtonBase>
  );
}

export default function Home() {
  const [prompt, setPrompt] = useState<ReactElement | undefined>(undefined);

  const { user } = useContext(UserContext);

  useEffect(() => {
    let filters = JSON.stringify({
      parent_id: { eq: null },
    });

    fetchJSON({
      url: "/api/v1/runs?limit=1&filters=" + filters,
      apiKey: user?.api_key,
      callback: (payload: RunListPayload) => {
        if (payload.content.length > 0) {
          const run = payload.content[0];
          setPrompt(
            <Typography
              fontSize="medium"
              component="span"
              sx={{ display: "flex", alignItems: "center" }}
            >
              Your latest run:&nbsp; <RunStateChip state={run.future_state} />
              <Link href={"/pipelines/" + run.calculator_path}>{run.name}</Link>
            </Typography>
          );
        }
      },
    });
  }, []);

  const h1 = user ? "Hi " + user.first_name : "Welcome to Sematic";

  return (
    <Container sx={{ pt: 10, height: "100vh", overflowY: "scroll" }}>
      {/*sx={{ pt: 20, mx: 5, height: "100vh", overflowY: "scroll" }}>*/}
      <Typography variant="h1">{h1}</Typography>
      <Box sx={{ mt: 15, mb: 10, minHeight: "1px" }}>
        {prompt ? (
          prompt
        ) : user ? (
          <Box sx={{ width: 600 }}>
            <Typography variant="h4" sx={{ mb: 4 }}>
              To get started, set your API key:
            </Typography>
            <ShellCommand
              command={"sematic settings set SEMATIC_API_KEY " + user.api_key}
            />
          </Box>
        ) : (
          <></>
        )}
      </Box>
      <Grid container>
        <Grid item xs sx={{ pr: 5, mt: 10 }}>
          <Typography variant="h3" sx={{ textAlign: "center" }}>
            Run an example pipeline
          </Typography>
          <Typography paragraph sx={{ mt: 10 }}>
            Sematic comes with a number of examples out-of-the box.
          </Typography>
          <Typography paragraph>Try the following:</Typography>
          <ShellCommand command={"sematic run examples/mnist/pytorch"} />
          <Typography paragraph sx={{ mt: 10 }}>
            Or any of the following:
          </Typography>
          <ul>
            <li>
              <Typography>
                <code>examples/mnist/pytorch</code>
              </Typography>
            </li>
            <li>
              <Typography>
                <code>examples/liver_cirrhosis</code>
              </Typography>
            </li>
          </ul>
          <Typography paragraph>
            Read more about examples on the{" "}
            <a href="https://docs.sematic.dev" target="blank">
              Sematic Documentation
            </a>
            .
          </Typography>
        </Grid>
        <Divider orientation="vertical" flexItem sx={{ my: 5 }} />

        <Grid item xs sx={{ px: 5, mt: 10 }}>
          <Typography variant="h3" sx={{ textAlign: "center" }}>
            Start your own project
          </Typography>
          <Typography paragraph sx={{ mt: 10 }}>
            Start a new Sematic project from a simple template:
          </Typography>
          <ShellCommand command={"sematic new my_new_project"} />
          <Typography paragraph sx={{ mt: 10 }}>
            Or start from one of the examples:
          </Typography>
          <ShellCommand
            command={"sematic new my_new_project --from examples/mnist/pytorch"}
          />
          <Typography paragraph sx={{ mt: 10 }}>
            Then simpy run:
          </Typography>
          <ShellCommand command={"python3 -m my_new_project"} />
        </Grid>
        <Divider orientation="vertical" flexItem sx={{ my: 5 }} />

        <Grid item xs sx={{ pl: 5, mt: 10 }}>
          <Typography variant="h3" sx={{ textAlign: "center" }}>
            Join the community
          </Typography>
          <Typography paragraph sx={{ mt: 10 }}>
            Get in touch on the following channels:
          </Typography>
          <Grid
            container
            sx={{ justifyContent: "center", alignItems: "flex-start", pt: 3 }}
            spacing={20}
          >
            <Grid item sx={{ textAlign: "center" }}>
              <Link
                href="https://discord.gg/PFCpatvy"
                underline="none"
                target="_blank"
              >
                <SiDiscord fontSize={42} color="#7289da" />
                <Typography>Discord</Typography>
              </Link>
            </Grid>
            <Grid item sx={{ textAlign: "center" }}>
              <Link
                href="https://github.com/sematic-ai/sematic"
                underline="none"
                target="_blank"
              >
                <SiGithub fontSize={42} color="#000000" />
                <Typography>GitHub</Typography>
              </Link>
            </Grid>
          </Grid>
          <Typography paragraph sx={{ mt: 10 }}>
            Check out the Sematic Documentation:
          </Typography>
          <Grid
            container
            sx={{ justifyContent: "center", alignItems: "flex-start", pt: 3 }}
          >
            <Grid item sx={{ textAlign: "center" }}>
              <Link
                href="https://docs.sematic.dev"
                underline="none"
                target="_blank"
              >
                <SiReadthedocs fontSize={38} color="#000000" />
                <Typography>Sematic Documentation</Typography>
              </Link>
            </Grid>
          </Grid>
          <Typography paragraph sx={{ mt: 10 }}>
            Or email us at{" "}
            <Link href="mailto:support@sematic.ai">support@sematic.ai</Link>.
          </Typography>
        </Grid>
      </Grid>
    </Container>
  );
}
