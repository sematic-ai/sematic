import { Table, TableCell, TableRow, TableBody } from "@mui/material";
import BoolValueView from "./boolean";
import { CommonValueViewProps, ReprValueView } from "./common";

export default function TorchDataLoaderValueView(props: CommonValueViewProps) {
    let { valueSummary } = props;
  
    return (
      <Table>
        <TableBody>
          <TableRow key="batch-size">
            <TableCell>
              <b>Batch size</b>
            </TableCell>
            <TableCell>{valueSummary["batch_size"]}</TableCell>
          </TableRow>
          <TableRow key="num_workers">
            <TableCell>
              <b>Number of suprocesses</b>
            </TableCell>
            <TableCell>{valueSummary["num_workers"]}</TableCell>
          </TableRow>
          <TableRow key="pin_memory">
            <TableCell>
              <b>Copy tensors into pinned memory</b>
            </TableCell>
            <TableCell>
              <BoolValueView
                {...props}
                valueSummary={valueSummary["pin_memory"]}
              />
            </TableCell>
          </TableRow>
          <TableRow key="timeout">
            <TableCell>
              <b>Timeout</b>
            </TableCell>
            <TableCell>{valueSummary["timeout"]} sec.</TableCell>
          </TableRow>
          <TableRow key="dataset">
            <TableCell>
              <b>Dataset</b>
            </TableCell>
            <TableCell>
              <ReprValueView {...props} valueSummary={valueSummary["dataset"]} />
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
    );
  }