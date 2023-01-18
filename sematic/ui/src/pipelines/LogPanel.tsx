import { Box, TextField } from "@mui/material";
import { useCallback, useState } from "react";
import { usePipelinePanelsContext } from "../hooks/pipelineHooks";
import ScrollingLogView from "./ScrollingLogView";

export default function LogPanel() {
  const { selectedRun } = usePipelinePanelsContext();
  const { id, external_exception_metadata_json, exception_metadata_json} = selectedRun!;
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
