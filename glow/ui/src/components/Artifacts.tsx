import { Artifact } from "../Models";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import Container from "@mui/material/Container";
import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import { renderSummary, renderType } from "../types/Types";

export function ArtifactList(props: { artifacts: Map<string, Artifact> }) {
  return (
    <List>
      {Array.from(props.artifacts).map(([name, artifact]) => (
        <ListItem key={name} sx={{ display: "block" }}>
          <Container sx={{ display: "flex", paddingX: 0 }}>
            {name !== "null" && (
              <Typography paddingRight={4}>{name}:</Typography>
            )}
            <Typography color="GrayText">
              {renderType(artifact.type_serialization)}
            </Typography>
          </Container>

          <Box sx={{ padding: 2 }}>
            {renderSummary(artifact.type_serialization, artifact.json_summary)}
          </Box>
        </ListItem>
      ))}
    </List>
  );
}
