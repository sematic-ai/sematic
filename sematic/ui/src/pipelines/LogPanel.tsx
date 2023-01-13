import { Box, TextField } from "@mui/material";
import { useCallback, useState } from "react";
import { Run } from "../Models";
import ScrollingLogView from "./ScrollingLogView";

export default function LogPanel(props: { run: Run }) {
  const { run } = props;
  const { id, external_exception_metadata_json, exception_metadata_json} = run;
  const [filterString, setFilterString] = useState<string>("");

  const onFilterStringChange = useCallback(
    (evt: any) => {
      setFilterString(evt.target.value);
    },
    [setFilterString]
  );

  return (
    <Box sx={{ display: "flex", flexGrow: 1 }} >
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column'}} >
        <TextField
          variant="standard"
          fullWidth={true}
          placeholder={"Filter..."}
          onChange={onFilterStringChange}
          style={{ flexShrink: 1 }}
        />
        <ScrollingLogView key={`${id}---${filterString}`} logSource={id}
          filterString={filterString}
          exception_metadata_json={exception_metadata_json} 
          external_exception_metadata_json={external_exception_metadata_json} />
      </Box>
    </Box>
  );
}
