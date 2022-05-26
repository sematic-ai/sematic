import { Artifact } from "../Models";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import Typography from "@mui/material/Typography";
import { renderSummary, renderType } from "../types/Types";
import { Table, TableBody, TableCell, TableRow } from "@mui/material";
import Id from "./Id";

export function ArtifactList(props: { artifacts: Map<string, Artifact> }) {
  return (
    <List>
      {Array.from(props.artifacts).map(([name, artifact]) => (
        <ListItem key={name} sx={{ display: "block", paddingLeft: 0 }}>
          <Table>
            <TableBody>
              {name !== "null" && (
                <TableRow>
                  <TableCell sx={{ verticalAlign: "top" }}>Name</TableCell>
                  <TableCell>
                    <b>{name}</b>
                  </TableCell>
                </TableRow>
              )}
              <TableRow>
                <TableCell sx={{ verticalAlign: "top" }}>ID</TableCell>
                <TableCell>
                  <Id id={artifact.id} />
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell sx={{ verticalAlign: "top" }}>Type</TableCell>
                <TableCell>
                  {" "}
                  <Typography color="GrayText" component="span">
                    {renderType(artifact.type_serialization.type)}
                  </Typography>
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell sx={{ verticalAlign: "top" }}>Value</TableCell>
                <TableCell>
                  {renderSummary(
                    artifact.type_serialization,
                    artifact.json_summary
                  )}
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </ListItem>
      ))}
    </List>
  );
}
