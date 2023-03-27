import { InfoOutlined } from "@mui/icons-material";
import { Alert, AlertTitle, Container, containerClasses, Skeleton } from "@mui/material";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { styled } from "@mui/system";
import { Run } from "@sematic/common/src/Models";
import { useCallback, useMemo } from "react";
import CalculatorPath from "src/components/CalculatorPath";
import MuiRouterLink from "src/components/MuiRouterLink";
import { RunList, RunListColumn } from "src/components/RunList";
import RunStateChip, { RunStateChipUndefinedStyle } from "src/components/RunStateChip";
import { RunTime } from "src/components/RunTime";
import Tags from "src/components/Tags";
import TimeAgo from "src/components/TimeAgo";
import useBasicMetrics from "src/hooks/metricsHooks";
import { useFetchRuns } from "src/hooks/pipelineHooks";
import { pipelineSocket } from "src/sockets";
import { runAvgRunTime, runSuccessRate } from "src/pipelines/BasicMetricsPanel";

const RecentStatusesWithStyles = styled('span')`
  flex-direction: row;
  display: flex;
`;

const StyledRootBox = styled(Box, {
  shouldForwardProp: () => true,
})`
  height: 100%;

  & .main-content {
    overflow-y: hidden;

    & .${containerClasses.root} {
      height: 100%;

      & > * {
        display: flex;
        flex-direction: column;
        height: 100%;
      }
    }
  }
`;

function PipelineMetric(props: {value: string, label: string}) {
  const {value, label} = props;
  return <Box sx={{textAlign: "center"}}>
    <Typography sx={{fontSize: 18}}>{value}</Typography>
    <Typography fontSize="small" color="Gray
    ">{label}</Typography>
  </Box>

}


function PipelineMetrics(props: {run: Run}) {
  const { run } = props;
  const [ payload, loading, error ] = useBasicMetrics({runId: run.id});

  const successRate = useMemo(() => payload ? runSuccessRate(payload.content.count_by_state, run) : "0%",
  [payload, run])

  const avgRuntime = useMemo(() => payload ? runAvgRunTime(payload.content.avg_runtime_children, run) : "0s"
  , [payload, run])

  return <>
  { loading === true && <Skeleton />}
  { loading !== true && error === undefined && payload && 
    <Box sx={{display: "flex", flexDirection: "row", columnGap: 5}}>
      <PipelineMetric value={payload.content.total_count.toString()} label="runs" />
      <PipelineMetric value={successRate} label="success" />
      <PipelineMetric value={avgRuntime} label="avg. time" />
    </Box>}
  </>;
}


const TableColumns: Array<RunListColumn> = [
  {name: "Name", width: "45%", render:(run: Run) => <PipelineNameColumn run={run} />},
  {name: "Last run", width: "20%", render:
  (run: Run) => <>
      <TimeAgo date={run.created_at} />
      <RunTime run={run} prefix="in" />
    </>},
  {name: "Metrics", width: "20%", render: (run: Run) => <PipelineMetrics run={run} />},
  {name: "Last 5 runs", width: "15%", render:
    ({calculator_path}: Run) => <RecentStatuses calculatorPath={calculator_path} />
}
]

function RecentStatuses(props: { calculatorPath: string }) {
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
      return <RunStateChip run={runs[index]} key={index} />;
    } else {
      return <RunStateChipUndefinedStyle key={index} />;
    }
  }
  if (isLoading) {
    return <Skeleton />
  }
  return <RecentStatusesWithStyles>
    {[...Array(5)].map((e, i) => statusChip(i))}
    </RecentStatusesWithStyles>;
}

function PipelineNameColumn(props: { run: Run }) {
  let { run } = props;
  let { calculator_path, name, tags } = run;

  return (  
    <>
      <Box sx={{ mb: 3 }}>  
        <MuiRouterLink href={"/pipelines/" + calculator_path} underline="hover">
          <Typography variant="h6">{name}</Typography>
        </MuiRouterLink>
        <CalculatorPath calculatorPath={calculator_path} />
      </Box>
      <Tags tags={tags || []} />
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
    <StyledRootBox sx={{ display: "grid", gridTemplateColumns: "1fr 300px" }}>
      <Box sx={{ gridColumn: 1 }} className={"main-content"}>
        <Container sx={{ pt: 15 }}>
          <Box sx={{ mx: 5 }}>
            <Box sx={{ mb: 10 }}>
              <Typography variant="h2" component="h2">
                Your pipelines
              </Typography>
            </Box>
            <RunList
              columns={TableColumns}
              groupBy="calculator_path"
              filters={{ AND: [{ parent_id: { eq: null } }] }}
              emptyAlert="No pipelines."
              triggerRefresh={triggerRefresh}
            />
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
    </StyledRootBox>
  );
}

export default PipelineIndex;
