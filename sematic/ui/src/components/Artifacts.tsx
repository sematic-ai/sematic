import { Artifact } from "../Models";
import Alert from "@mui/material/Alert";
import AlertTitle from "@mui/material/AlertTitle";
import { renderSummary } from "../types/Types";
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableRow,
  useTheme,
} from "@mui/material";
import { ErrorBoundary } from "react-error-boundary";
import { CopyButton } from "./CopyButton";

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

  const theme = useTheme();

  return (
    <Box sx={{ fontSize: "small", color: theme.palette.grey[400] }}>
      <code>{artifactId.substring(0, 6)}</code>
      <CopyButton text={artifactId} message="Copied Artifact ID." />
    </Box>
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
