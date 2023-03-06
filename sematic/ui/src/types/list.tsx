import { Table, TableBody, TableRow, TableCell } from "@mui/material";
import Alert from "@mui/material/Alert";
import Typography from "@mui/material/Typography";
import { AliasValueViewProps, renderSummary } from "./common";

export default function ListValueView(props: AliasValueViewProps) {
  let typeRepr = props.typeRepr;
  if (!typeRepr[2].args) {
    return <Alert severity="error">Incorrect type serialization</Alert>;
  }

  let elementTypeRepr = typeRepr[2].args[0].type;
  const summaryIsEmpty = props.valueSummary["summary"].length === 0;

  const summaryIsComplete =
    props.valueSummary["summary"].length === props.valueSummary["length"];

  var summary;
  if (summaryIsEmpty) {
    summary = (
      <Typography display="inline" component="span" fontStyle={"italic"}>
        Nothing to display
      </Typography>
    );
  } else {
    summary = (
      <Typography display="inline" component="span">
        [
        {Array.from(props.valueSummary["summary"])
          .map<React.ReactNode>((element, index) =>
            renderSummary(
              props.typeSerialization,
              element,
              elementTypeRepr,
              index.toString()
            )
          )
          .reduce((prev, curr) => [prev, ", ", curr])}
        ]
      </Typography>
    );
  }

  if (summaryIsComplete && !summaryIsEmpty) return summary;

  return (
    <Table>
      <TableBody>
        <TableRow>
          <TableCell>
            <b>Total elements</b>
          </TableCell>
          <TableCell>{props.valueSummary["length"]}</TableCell>
        </TableRow>
        <TableRow>
          <TableCell>
            <b>Excerpt</b>
          </TableCell>
          <TableCell>
            {summary} and{" "}
            {props.valueSummary["length"] -
              props.valueSummary["summary"].length}{" "}
            more items.
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  );
}