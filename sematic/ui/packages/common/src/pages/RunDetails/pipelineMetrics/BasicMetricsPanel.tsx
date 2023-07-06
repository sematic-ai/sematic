import styled from "@emotion/styled";
import HelpIcon from "@mui/icons-material/Help";
import {
    Alert,
    Box,
    ButtonBase,
    Grid,
    Table,
    TableBody,
    TableCell,
    TableRow,
    Typography,
} from "@mui/material";
import useBasicMetrics from "src/hooks/metricsHooks";
import { theme } from "src/theme/mira/index";
import { durationSecondsToString } from "src/utils/datetime";
import { useMemo, useEffect } from "react";
import ImportPath from "src/component/ImportPath";

const MetricBox = styled(Box)`
  text-align: center;
  padding: ${theme.spacing(10)};
`;

const MetricValue = styled(Typography)`
  font-size: 70px;
  font-weight: 500;
  line-height: 1;
`;

const MetricLabel = styled(Box)`
  display: flex;
  flex-direction: row;
  align-items: center;
  column-gap: ${theme.spacing(1)};
  justify-content: center;

  & .MuiTypography-root {
    font-size: 20px;
  }

  & .MuiSvgIcon-root {
    color: ${theme.palette.grey[300]};
  }
`;

function TopMetric(props: { value: string; label: string; docs?: string }) {
    const { value, label, docs } = props;

    return (
        <MetricBox>
            <MetricValue sx={{ fontSize: 70, fontWeight: 500, lineHeight: 1 }}>
                {value}
            </MetricValue>
            <MetricLabel>
                <Typography>{label}</Typography>
                {docs !== undefined && (
                    <ButtonBase
                        href={`https://docs.sematic.dev/diving-deeper/metrics#${docs}`}
                        target="_blank"
                    >
                        <HelpIcon fontSize="small" />
                    </ButtonBase>
                )}
            </MetricLabel>
        </MetricBox>
    );
}

interface BasicMetricsPanelProps {
    runId: string,
    functionPath: string,
    setIsLoading: (isLoading: boolean) => void
}

export default function BasicMetricsPanel(props: BasicMetricsPanelProps) {
    const { runId, functionPath, setIsLoading } = props;

    const { payload, loading, error, totalCount, successRate, avgRuntime }
        = useBasicMetrics({ runId, rootFunctionPath: functionPath });

    const sortedAvgRuntimeChildren = useMemo(
        () =>
            Object.entries(payload?.content.avg_runtime_children || {}).sort((a, b) =>
                a[1] > b[1] ? -1 : 1
            ),
        [payload]
    );

    useEffect(() => {
        setIsLoading(loading);
    }, [loading, setIsLoading]);

    return (
        <Box sx={{ p: 5 }}>
            {!loading && error !== undefined && (
                <Alert severity="error">Unable to load metrics: {error.message}</Alert>
            )}
            {!loading && !error && payload !== undefined && (
                <>
                    <Typography variant="h1">Pipeline Metrics</Typography>
                    <Grid container sx={{ my: 10 }}>
                        <Grid item xs={4}>
                            <TopMetric
                                value={`${totalCount}`}
                                label="runs"
                                docs="run-count"
                            />
                        </Grid>
                        <Grid item xs={4}>
                            <TopMetric
                                value={successRate}
                                label="success rate"
                                docs="success-rate"
                            />
                        </Grid>
                        <Grid item xs={4}>
                            <TopMetric
                                value={avgRuntime}
                                label="avg. run time"
                                docs="average-run-time"
                            />
                        </Grid>
                    </Grid>
                    <Typography variant="h3">Average run time by function</Typography>
                    <Box sx={{ my: 10 }}>
                        <Table>
                            <TableBody>
                                {sortedAvgRuntimeChildren.map(
                                    ([functionPath, runtimeS], idx) => (
                                        <TableRow key={idx}>
                                            <TableCell>
                                                <ImportPath>{functionPath}</ImportPath>
                                            </TableCell>
                                            <TableCell>{durationSecondsToString(runtimeS)}</TableCell>
                                        </TableRow>
                                    )
                                )}
                            </TableBody>
                        </Table>
                    </Box>
                </>
            )}
        </Box>
    );
}
