import { Artifact } from "../Models";
import List from "@mui/material/List";
import Alert from "@mui/material/Alert";
import AlertTitle from "@mui/material/AlertTitle";
import ListItem from "@mui/material/ListItem";
import Typography from "@mui/material/Typography";
import { renderSummary, renderType } from "../types/Types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@mui/material";
import Id from "./Id";
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
  return <></>;
  /*return (
    <>
      {props.artifacts.size === 0 && <Alert severity="info">No values</Alert>}
      <List>
        {Array.from(props.artifacts).map(([name, artifact]) => (
          <ListItem key={name} sx={{ display: "block", paddingLeft: 0 }}>
            <Table>
              {name !== "null" && (
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ verticalAlign: "top" }}>Name</TableCell>
                    <TableCell>
                      <b>{name}</b>
                    </TableCell>
                  </TableRow>
                </TableHead>
              )}
              <TableBody>
                <TableRow>
                  <TableCell sx={{ verticalAlign: "top" }}>Value</TableCell>
                  <TableCell>
                    <ErrorBoundary FallbackComponent={ArtifactError}>
                      {artifact &&
                        renderSummary(
                          artifact.type_serialization,
                          artifact.json_summary
                        )}
                    </ErrorBoundary>
                  </TableCell>
                </TableRow>
              </TableBody>
              <TableRow>
                <TableCell sx={{ verticalAlign: "top" }}>Type</TableCell>
                <TableCell>
                  <ErrorBoundary FallbackComponent={ArtifactError}>
                    {artifact && (
                      <Typography color="GrayText" component="span">
                        {renderType(artifact.type_serialization.type)}
                      </Typography>
                    )}
                  </ErrorBoundary>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell sx={{ verticalAlign: "top" }}>ID</TableCell>
                <TableCell>{artifact && <Id id={artifact.id} />}</TableCell>
              </TableRow>
            </Table>
          </ListItem>
        ))}
      </List>
    </>
  );*/
}
