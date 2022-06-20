import { ContentCopy } from "@mui/icons-material";
import {
  ButtonBase,
  Container,
  Grid,
  Typography,
  useTheme,
} from "@mui/material";
import { useCallback, useState } from "react";

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
  const theme = useTheme();

  return (
    <Container sx={{ mt: 20, mx: 5 }}>
      <Typography variant="h1">🦊 Welcome to Sematic!</Typography>
      <Grid container sx={{ mt: 20 }}>
        <Grid item xs={12} md={4} sx={{ px: 5 }}>
          <Typography variant="h3" sx={{ mb: 3 }}>
            Run an example pipeline
          </Typography>
          <Typography paragraph>
            Sematic comes with a number of examples out-of-the box.
          </Typography>
          <Typography paragraph>Try the following:</Typography>
          <ShellCommand command={"sematic run examples/mnist/pytorch"} />
          <Typography paragraph sx={{ mt: 3 }}>
            Or any of the following:
            <ul>
              <li>
                <code>examples/mnist/pytorch</code>
              </li>
              <li>
                <code>examples/liver_cirrhosis</code>
              </li>
            </ul>
          </Typography>
          <Typography paragraph>
            Read more about examples on the{" "}
            <a href="https://docs.sematic.ai" target="blank">
              Sematic Documentation
            </a>
            .
          </Typography>
        </Grid>
        <Grid item xs={12} md={4} sx={{ borderLeft: 1, px: 5, borderColor:  }}>
          <Typography variant="h3">Write your own</Typography>
        </Grid>
        <Grid item xs={12} md={4} sx={{ borderLeft: 1, px: 5 }}>
          <Typography variant="h3">Join the community</Typography>
        </Grid>
      </Grid>
    </Container>
  );
}
