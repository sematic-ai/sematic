import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableRow,
  useTheme
} from "@mui/material";
import Alert from "@mui/material/Alert";
import AlertTitle from "@mui/material/AlertTitle";
import { Artifact } from "@sematic/common/src/Models";
import { useEffect, useMemo, useRef } from "react";
import { ErrorBoundary } from "react-error-boundary";
import CopyButton from "@sematic/common/src/component/CopyButton";
import { usePipelinePanelsContext } from "src/hooks/pipelineHooks";
import { renderSummary } from "src/types/Types";

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
    <ErrorBoundary resetKeys={[artifact.id]} FallbackComponent={ArtifactError}>
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

  const { selectedArtifactName } = usePipelinePanelsContext();

  const refs = useRef(new Array(artifacts.size));
  const artifactIds = useMemo(()=>Array.from(artifacts.keys()), [artifacts]);

  useEffect(()=>{
    if (selectedArtifactName !== "") {
      const selectedRefIdx = artifactIds.indexOf(selectedArtifactName);
      refs.current[selectedRefIdx]?.scrollIntoView({ behavior: "smooth" });
    }
  }, [artifactIds, selectedArtifactName]);

  if (artifacts.size === 0) {
    return <Alert severity="info">No values</Alert>;
  }

  if (artifacts.size === 1 && Array.from(artifacts.keys())[0] === "null") {
    let artifact = artifacts.get("null");
    return <>{artifact && <div ref={el => refs.current[0] = el} ><ArtifactView artifact={artifact} /></div>}</>;
  } else {
    return (
      <Table>
        <TableBody>
          {Array.from(artifacts).map(([name, artifact], idx) => (
            <TableRow key={name} ref={el => refs.current[idx] = el}>
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
