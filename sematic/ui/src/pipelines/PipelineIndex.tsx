import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import TableCell from "@mui/material/TableCell";
import TableRow from "@mui/material/TableRow";
import { useCallback, useMemo } from "react";
import { RunList } from "../components/RunList";
import Tags from "../components/Tags";
import { Run } from "../Models";
import RunStateChip, { RunStateChipUndefinedStyle } from "../components/RunStateChip";
import { Alert, AlertTitle, Container, containerClasses } from "@mui/material";
import { InfoOutlined } from "@mui/icons-material";
import { RunTime } from "../components/RunTime";
import CalculatorPath from "../components/CalculatorPath";
import TimeAgo from "../components/TimeAgo";
import { useFetchRuns } from "../hooks/pipelineHooks";
import Loading from "../components/Loading";
import { styled } from "@mui/system";
import MuiRouterLink from "../components/MuiRouterLink";
import { pipelineSocket } from "../sockets";

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

const TableColumns = [
  {name: "Name", width: "65%"},
  {name: "Last run", width: "20%"},
  {name: "Status", width: "15%"}
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

function PipelineRow(props: { run: Run }) {
  let { run }  = props;
  let { id, name, tags, calculator_path, created_at} = run;

  return (
    <>
      <TableRow key={id}>
        <TableCell key="name" data-cy={"pipeline-row"}>
          <Box sx={{ mb: 3 }}>
            <MuiRouterLink href={"/pipelines/" + calculator_path} underline="hover">
              <Typography variant="h6">{name}</Typography>
            </MuiRouterLink>
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
    </StyledRootBox>
  );
}

export default PipelineIndex;
