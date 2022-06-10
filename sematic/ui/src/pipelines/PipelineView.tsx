import Box from "@mui/material/Box";
import { useState, useCallback } from "react";
import { Run } from "../Models";
import Loading from "../components/Loading";
import Tags from "../components/Tags";
import { useParams } from "react-router-dom";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";
import { RunList, RunFilterType } from "../components/RunList";
import { RunRow } from "../runs/RunIndex";
import CalculatorPath from "../components/CalculatorPath";
import { pipelineSocket } from "../utils";
import DagTab from "../components/DagTab";
import Docstring from "../components/Docstring";

export default function PipelineView() {
  const [error, setError] = useState<Error | undefined>(undefined);
  const [selectedRun, setSelectedRun] = useState<Run | undefined>(undefined);
  const [isLoaded, setIsLoaded] = useState(false);

  let params = useParams();

  let { calculatorPath } = params;

  const triggerRefresh = useCallback(
    (refreshCallback: () => void) => {
      pipelineSocket.removeAllListeners();
      pipelineSocket.on("update", (args: { calculator_path: string }) => {
        if (args.calculator_path === calculatorPath) {
          refreshCallback();
        }
      });
    },
    [calculatorPath]
  );

  const onRowClick = useCallback(
    (run: Run) => {
      if (selectedRun?.id !== run.id) {
        setSelectedRun(run);
      }
    },
    [selectedRun]
  );

  const onRunsLoaded = useCallback(
    (runs: Run[]) => {
      if (runs.length > 0) {
        if (selectedRun === undefined) {
          setSelectedRun(runs[0]);
          setIsLoaded(true);
        }
      } else {
        setError(Error("No such pipeline."));
      }
    },
    [selectedRun]
  );

  if (calculatorPath === undefined) {
    setError(Error("undefined function path"));
  } else if (error === undefined) {
    let runFilters: RunFilterType = {
      AND: [
        { parent_id: { eq: null } },
        { calculator_path: { eq: calculatorPath } },
      ],
    };
    return (
      <>
        {selectedRun && (
          <Box marginTop={2} marginBottom={12}>
            <Box marginBottom={3}>
              <Typography variant="h3" component="h2">
                {selectedRun.name}
              </Typography>
              <CalculatorPath calculatorPath={selectedRun.calculator_path} />
            </Box>
            <Box>
              <Tags tags={selectedRun.tags || []} />
            </Box>
            <Grid container>
              <Grid item xs={6}>
                <Box marginY={3}>
                  <Docstring docstring={selectedRun.description} />
                </Box>
              </Grid>
              <Grid item xs={6}></Grid>
            </Grid>
          </Box>
        )}
        <Typography variant="h6" component="h3">
          Latest runs
        </Typography>
        <RunList
          columns={["ID", "Name", "Tags", "Time", "Status"]}
          filters={runFilters}
          pageSize={5}
          size="small"
          onRunsLoaded={(runs: Run[]) => onRunsLoaded(runs)}
          triggerRefresh={triggerRefresh}
        >
          {(run: Run) => (
            <RunRow
              run={run}
              key={run.id}
              variant="skinny"
              onClick={(e) => onRowClick(run)}
              selected={selectedRun?.id === run.id}
              noRunLink
            />
          )}
        </RunList>
        {selectedRun && (
          <Box paddingY={10}>
            <DagTab rootRun={selectedRun} />
          </Box>
        )}
      </>
    );
  }
  return <Loading error={error} isLoaded={isLoaded} />;
}
