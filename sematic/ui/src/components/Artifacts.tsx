import { Artifact } from "../Models";
import Alert from "@mui/material/Alert";
import AlertTitle from "@mui/material/AlertTitle";
import { renderSummary } from "../types/Types";
import { Table, TableBody, TableCell, TableRow } from "@mui/material";
import { ErrorBoundary } from "react-error-boundary";

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
      {renderSummary(artifact.type_serialization, artifact.json_summary)}
    </ErrorBoundary>
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
