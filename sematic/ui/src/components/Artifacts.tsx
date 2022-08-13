import { Artifact } from "../Models";
import Alert from "@mui/material/Alert";
import AlertTitle from "@mui/material/AlertTitle";
import { renderSummary } from "../types/Types";
import {
  Box,
  ButtonBase,
  Table,
  TableBody,
  TableCell,
  TableRow,
  useTheme,
} from "@mui/material";
import { ErrorBoundary } from "react-error-boundary";
import { ContentCopy, Help, HelpOutline } from "@mui/icons-material";
import { useCallback, useState } from "react";

function ArtifactError(props: { error: Error }) {
  return (
    <Alert severity="error">
      <AlertTitle>
        There was an error rendering this artifact. Please report the following
        error to Discord.
      </AlertTitle>
      {props.error.message}
    </Alert>
  );
}

function ArtifactView(props: { artifact: Artifact }) {
  let { artifact } = props;
  return (
    <ErrorBoundary FallbackComponent={ArtifactError}>
      <Box>
        <Box sx={{ float: "right" }}>
          <ArtifactID artifactId={artifact.id} />
        </Box>
        {renderSummary(artifact.type_serialization, artifact.json_summary)}
      </Box>
    </ErrorBoundary>
  );
}

function ArtifactID(props: { artifactId: string }) {
  const { artifactId } = props;

  const [content, setContent] = useState(artifactId.substring(0, 6));

  const theme = useTheme();

  const copy = useCallback(() => {
    navigator.clipboard.writeText(artifactId);
    setContent("Copied");
    setTimeout(() => setContent(artifactId.substring(0, 6)), 1000);
  }, [artifactId]);

  return (
    <ButtonBase
      sx={{ color: theme.palette.grey[400], fontSize: 12 }}
      onClick={copy}
    >
      <code>{content}</code>
    </ButtonBase>
  );
}

export function ArtifactList(props: {
  artifacts: Map<string, Artifact | undefined>;
}) {
  let { artifacts } = props;

  if (artifacts.size === 0) {
    return <Alert severity="info">No values</Alert>;
  }
  if (artifacts.size === 1 && Array.from(artifacts.keys())[0] === "null") {
    let artifact = artifacts.get("null");
    return <>{artifact && <ArtifactView artifact={artifact} />}</>;
  } else {
    return (
      <Table>
        <TableBody>
          {Array.from(artifacts).map(([name, artifact]) => (
            <TableRow key={name}>
              <TableCell sx={{ verticalAlign: "top" }}>
                <b>{name}</b>
              </TableCell>
              <TableCell>
                {artifact && <ArtifactView artifact={artifact} />}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    );
  }
}
