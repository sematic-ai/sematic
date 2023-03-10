import { InfoOutlined } from "@mui/icons-material";
import { Alert, AlertTitle, Container, containerClasses } from "@mui/material";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { styled } from "@mui/system";
import { Run } from "@sematic/common/src/Models";
import { useCallback, useMemo } from "react";
import CalculatorPath from "src/components/CalculatorPath";
import Loading from "src/components/Loading";
import MuiRouterLink from "src/components/MuiRouterLink";
import { RunList, RunListColumn } from "src/components/RunList";
import RunStateChip, { RunStateChipUndefinedStyle } from "src/components/RunStateChip";
import { RunTime } from "src/components/RunTime";
import Tags from "src/components/Tags";
import TimeAgo from "src/components/TimeAgo";
import { useFetchRuns } from "src/hooks/pipelineHooks";
import { pipelineSocket } from "src/sockets";

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

const TableColumns: Array<RunListColumn> = [
  {name: "Name", width: "65%", render:(run: Run) => <PipelineNameColumn run={run} />},
  {name: "Last run", width: "20%", render:
    (run: Run) => <>
      <TimeAgo date={run.created_at} />
      <RunTime run={run} prefix="in" />
    </>},
  {name: "Status", width: "15%", render:
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
    return <Loading isLoaded={false} /> 
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
