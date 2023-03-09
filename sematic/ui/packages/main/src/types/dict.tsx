
import { Table, TableCell, TableRow, TableBody, TableHead } from "@mui/material";
import { AliasValueViewProps, renderSummary } from "./common";

export default function DictValueView(props: AliasValueViewProps) {
  let typeRepr = props.typeRepr;

  let keyTypeRepr = typeRepr[2].args[0].type;
  let valueTypeRepr = typeRepr[2].args[1].type;

  let valueSummary = props.valueSummary as [any, any];

  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableCell>key</TableCell>
          <TableCell>value</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {Array.from(valueSummary).map((pair, index) => (
          <TableRow key={index}>
            <TableCell>
              {renderSummary(props.typeSerialization, pair[0], keyTypeRepr)}
            </TableCell>
            <TableCell>
              {renderSummary(props.typeSerialization, pair[1], valueTypeRepr)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}