import { MetricsFilter, useAggregatedMetrics } from "src/hooks/metricsHooks";
import {
  Alert,
  Box,
  ButtonBase,
  Skeleton,
  SxProps,
  Table,
  TableBody,
  TableCell,
  TableRow,
  Typography,
} from "@mui/material";
import { ReactElement, useCallback, useMemo } from "react";
import { durationSecondsToString } from "src/utils";
import HelpIcon from "@mui/icons-material/Help";
import styled from "@emotion/styled";
import { theme } from "@sematic/common/src/theme/mira/index";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartData,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const MetricBox = styled(Box)`
  text-align: center;
`;

const MetricLabel = styled(Box)`
  display: flex;
  flex-direction: row;
  align-items: center;
  column-gap: ${theme.spacing(1)};
  justify-content: center;

  & .MuiSvgIcon-root {
    color: ${theme.palette.grey[300]};
  }
`;

export function ScalarMetric(props: {
  metricsFilter: MetricsFilter;
  label: string;
  docs?: string;
  formatValue?: (value: number) => string;
  variant?: "small" | "large";
  live?: boolean;
}) {
  const { metricsFilter, label, docs, formatValue, variant = "small" } = props;
  const [payload, loading, error] = useAggregatedMetrics(metricsFilter);

  const value = useMemo(() => {
    if (payload === undefined) return undefined;
    return payload.content.series[0][0];
  }, [payload]);

  const valueToString = useCallback(
    (value: number): string => {
      if (formatValue !== undefined) {
        return formatValue(value);
      }
      return value.toString();
    },
    [formatValue]
  );

  const valueStyle = useMemo<SxProps>(() => {
    if (variant === "large")
      return {
        fontSize: 70,
        fontWeight: 500,
        lineHeight: 1,
      };
    return {
      fontSize: 20,
    };
  }, [variant]);

  const labelStyle = useMemo<SxProps>(() => {
    if (variant === "small")
      return {
        fontSize: 12,
        color: "Gray",
      };
    return {
      fontSize: 20,
    };
  }, [variant]);

  return (
    <MetricBox>
      {loading && <Skeleton />}
      {!loading && (
        <Typography sx={valueStyle}>
          {error !== undefined && "-"}
          {value !== undefined && valueToString(value)}
        </Typography>
      )}
      <MetricLabel>
        <Typography sx={labelStyle}>{label}</Typography>
        {docs !== undefined && variant !== "small" && (
          <ButtonBase
            href={`https://docs.sematic.dev/diving-deeper/metrics#${docs}`}
            target="_blank"
          >
            <HelpIcon fontSize="small" sx={{}} />
          </ButtonBase>
        )}
      </MetricLabel>
    </MetricBox>
  );
}

export function TimeseriesMetric(props: {
  metricsFilter: MetricsFilter;
  color: string;
}) {
  const { metricsFilter, color } = props;
  const [payload, loading, error] = useAggregatedMetrics(metricsFilter);

  const chartData = useMemo(() => {
    const cData: ChartData<"line", number[], string> = {
      labels: [],
      datasets: [
        {
          label: metricsFilter.metricName,
          data: [],
          backgroundColor: color,
          borderColor: color,
        },
      ],
    };
    if (payload === undefined) return cData;

    payload.content.series.forEach((item) => {
      cData.labels?.push(item[1][0]);
      cData.datasets[0].data.push(item[0]);
    });

    return cData;
  }, [payload]);

  return (
    <>
      {loading && <Skeleton />}
      {error && (
        <Alert severity="error">Unable to load metric: {error.message}</Alert>
      )}
      {payload !== undefined && <Line data={chartData} />}
    </>
  );
}

export function ListMetric(props: {
  metricsFilter: MetricsFilter;
  formatValue?: (value: number) => string;
  formatLabel?: (name: string, value: any) => ReactElement;
  sortSeries?: (a: [number, any[]], b: [number, any[]]) => number;
}) {
  const { metricsFilter, formatValue, formatLabel, sortSeries } = props;
  const [payload, loading, error] = useAggregatedMetrics(metricsFilter);

  const sortFn = useCallback(
    (a: [number, any[]], b: [number, any[]]): number => {
      if (sortSeries !== undefined) return sortSeries(a, b);
      return 0;
    },
    [sortSeries]
  );

  const series = useMemo(() => {
    if (payload === undefined) return undefined;
    return payload.content.series.sort(sortFn);
  }, [payload]);

  const groupByLabels = useMemo(
    () => (payload !== undefined ? payload.content.group_by_labels : undefined),
    [payload]
  );

  const valueToString = useCallback(
    (value: number): string => {
      if (formatValue !== undefined) {
        return formatValue(value);
      }
      return value.toString();
    },
    [formatValue]
  );

  const labelToElement = useCallback(
    (name: string, value: any): ReactElement => {
      if (formatLabel !== undefined) {
        return formatLabel(name, value);
      }
      return <Typography>{value}</Typography>;
    },
    [formatLabel]
  );

  return (
    <>
      {loading && <Skeleton />}
      {error !== undefined && (
        <Alert severity="error">Unable to load metrics.</Alert>
      )}
      {series !== undefined && (
        <Table>
          <TableBody>
            {series.map((value) => (
              <TableRow>
                {groupByLabels?.map((label, idx) => (
                  <TableCell key={idx}>
                    {labelToElement(label, value[1][idx])}
                  </TableCell>
                ))}
                <TableCell>{valueToString(value[0])}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </>
  );
}

export function FuncRunCountMetric(props: {
  variant?: "small" | "large";
  calculatorPath: string;
}) {
  const { variant, calculatorPath } = props;

  const runCountFilter = useMemo<MetricsFilter>(() => {
    return {
      metricName: "sematic.run_count",
      labels: { calculator_path: calculatorPath },
      groupBys: [],
    };
  }, [calculatorPath]);

  return (
    <ScalarMetric
      metricsFilter={runCountFilter}
      label="runs"
      docs="run-count"
      variant={variant}
    />
  );
}

export function FuncSuccessRateMetric(props: {
  variant?: "small" | "large";
  calculatorPath: string;
}) {
  const { variant, calculatorPath } = props;

  const runCountFilter = useMemo<MetricsFilter>(() => {
    return {
      metricName: "sematic.func_success_rate",
      labels: { calculator_path: calculatorPath },
      groupBys: [],
    };
  }, [calculatorPath]);

  return (
    <ScalarMetric
      metricsFilter={runCountFilter}
      label="success"
      docs="success-rate"
      variant={variant}
      formatValue={floatToPercent}
    />
  );
}

export function FuncAvgRuntimeMetric(props: {
  variant?: "small" | "large";
  calculatorPath: string;
}) {
  const { variant, calculatorPath } = props;

  const runCountFilter = useMemo<MetricsFilter>(() => {
    return {
      metricName: "sematic.func_effective_runtime",
      labels: { calculator_path: calculatorPath },
      groupBys: [],
    };
  }, [calculatorPath]);

  return (
    <ScalarMetric
      metricsFilter={runCountFilter}
      label="avg. runtime"
      docs="average-run-time"
      variant={variant}
      formatValue={durationSecondsToString}
    />
  );
}

const floatToPercent = (value: number) => `${Math.floor(value * 100)}%`;
