import { Artifact } from "../Models";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import Container from "@mui/material/Container";
import Typography from "@mui/material/Typography";
import { renderSummary, renderType } from "../types/Types";

export function ArtifactList(props: { artifacts: Map<string, Artifact> }) {
  return (
    <List>
      {Array.from(props.artifacts).map(([name, artifact]) => (
        <ListItem key={name} sx={{ display: "block", paddingLeft: 0 }}>
          <Container sx={{ display: "flex", paddingX: 0 }}>
            {name !== "null" && (
              <Typography paddingRight={4}>{name}:</Typography>
            )}
            <Typography color="GrayText">
              {renderType(artifact.type_serialization.type)}
            </Typography>
          </Container>

          <Container>
            {renderSummary(artifact.type_serialization, artifact.json_summary)}
          </Container>
        </ListItem>
      ))}
    </List>
  );
}
