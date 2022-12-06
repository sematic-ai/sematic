import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import TableCell from "@mui/material/TableCell";
import TableRow from "@mui/material/TableRow";
import { useCallback, useMemo } from "react";
import { RunList } from "../components/RunList";
import Tags from "../components/Tags";
import { Run } from "../Models";
import Link from "@mui/material/Link";
import RunStateChip from "../components/RunStateChip";
import { Alert, AlertTitle, Container } from "@mui/material";
import { InfoOutlined } from "@mui/icons-material";
import { RunTime } from "../components/RunTime";
import { pipelineSocket } from "../utils";
import CalculatorPath from "../components/CalculatorPath";
import TimeAgo from "../components/TimeAgo";
import { useFetchRuns } from "../hooks/pipelineHooks";
import Loading from "../components/Loading";

function RecentStatuses(props: { calculatorPath: string }) {
  let state: string | undefined = undefined;
  const { calculatorPath } = props;

  const runFilters = useMemo(() => ({
    calculator_path: { eq: calculatorPath },
  }), [calculatorPath]);

  const otherQueryParams = useMemo(() => ({
      limit: '5'
  }), []);

  const {isLoading, runs } = useFetchRuns(runFilters, otherQueryParams);

  function statusChip(index: number) {
    if (runs && runs.length > index) {
      state = runs[index].future_state;
    } else {
      state = "undefined";
    }
    return <RunStateChip state={state} key={index} />;
  }
  if (isLoading) {
    return <Loading isLoaded={false} /> 
  }
  return <>{[...Array(5)].map((e, i) => statusChip(i))}</>;
}

function PipelineRow(props: { run: Run }) {
  let { run }  = props;
  let { id, name, tags, calculator_path, created_at} = run;

  return (
    <>
      <TableRow key={id}>
        <TableCell key="name">
          <Box sx={{ mb: 3 }}>
            <Link href={"/pipelines/" + calculator_path} underline="hover">
              <Typography variant="h6">{name}</Typography>
            </Link>
            <CalculatorPath calculatorPath={calculator_path} />
          </Box>
          <Tags tags={tags || []} />
        </TableCell>
        <TableCell key="last-run">
          <TimeAgo date={created_at} />
          <RunTime run={run} prefix="in" />
        </TableCell>
        <TableCell key="status" width={120}>
          <RecentStatuses calculatorPath={calculator_path} />
        </TableCell>
      </TableRow>
    </>
  );
}

function PipelineIndex() {
  const triggerRefresh = useCallback((refreshCallback: () => void) => {
    pipelineSocket.removeAllListeners();
    pipelineSocket.on("update", (args) => {
      refreshCallback();
    });
  }, []);

  return (
    <Box sx={{ display: "grid", gridTemplateColumns: "1fr 300px" }}>
      <Box sx={{ gridColumn: 1 }}>
        <Container sx={{ pt: 15 }}>
          <Box sx={{ mx: 5 }}>
            <Box sx={{ mb: 10 }}>
              <Typography variant="h2" component="h2">
                Your pipelines
              </Typography>
            </Box>
            <RunList
              columns={["Name", "Last run", "Status"]}
              groupBy="calculator_path"
              filters={{ AND: [{ parent_id: { eq: null } }] }}
              emptyAlert="No pipelines."
              triggerRefresh={triggerRefresh}
            >
              {(run: Run) => <PipelineRow run={run} key={run.id} />}
            </RunList>
          </Box>
        </Container>
      </Box>
      <Box sx={{ gridColumn: 2, pr: 5, pt: 45 }}>
        <Alert severity="warning" icon={<InfoOutlined />}>
          <AlertTitle>Your latest pipelines are listed here</AlertTitle>
          <p>
            Pipelines are identified by the import path of their entry point,
            which is the function you called <code>.resolve()</code> on.
          </p>
        </Alert>
      </Box>
    </Box>
  );
}

export default PipelineIndex;
