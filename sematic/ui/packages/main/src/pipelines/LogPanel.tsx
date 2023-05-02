import { Box, TextField } from "@mui/material";
import { useCallback, useState } from "react";
import { usePipelinePanelsContext } from "../hooks/pipelineHooks";
import BidirectionalLogView from "src/components/BidirectionalLogView";

export default function LogPanel() {
  const { selectedRun } = usePipelinePanelsContext();
  const { id } = selectedRun!;
  const [filterString, setFilterString] = useState<string>("");

  const onFilterStringChange = useCallback(
    (evt: any) => {
      setFilterString(evt.target.value);
    },
    [setFilterString]
  );

  return (
    <Box >
      <Box sx={{ display: 'flex', flexDirection: 'column'}} >
        <TextField
          variant="standard"
          fullWidth={true}
          placeholder={"Filter..."}
          onChange={onFilterStringChange}
          style={{ flexShrink: 1 }}
        />
        <BidirectionalLogView key={`${id}---${filterString}`} logSource={id}
          filterString={filterString} />
      </Box>
    </Box>
  );
}
