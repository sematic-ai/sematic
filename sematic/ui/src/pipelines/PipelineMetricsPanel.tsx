import { Alert, AlertTitle, Box, Typography } from "@mui/material";
import { useMemo } from "react";
import Loading from "src/components/Loading";
import { ExtractContextType } from "src/components/utils/typings";
import { Run } from "src/Models";
import { usePipelineRunContext } from "../hooks/pipelineHooks";
import PipelineRunViewContext from "./PipelineRunViewContext";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartData
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import useMetrics from "src/hooks/metricsHooks";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const COLORS = [
  'rgb(255, 99, 132)',
  'rgb(54, 162, 235)',
  'rgb(255, 206, 86)',
  'rgb(75, 192, 192)',
  'rgb(153, 102, 255)',
  'rgb(255, 159, 64)'
];

export default function PipelineMetricsPanel() {
  const { rootRun } = usePipelineRunContext () as ExtractContextType<typeof PipelineRunViewContext > & {
    rootRun: Run
  };

  const [ payload, loading, error ] = useMetrics({calculatorPath: rootRun.calculator_path});

  const metrics = useMemo(() => {
    return payload?.content;
  }, [payload]);

  const graphDataByName = useMemo(() => {
    if (metrics === undefined) {
      return undefined;
    }
    let colorIndex = 0;
    let dataByName: Map<string, ChartData<"line", number[], string>> = new Map();
    Object.entries(metrics).forEach(([name, byRootId]) => {
      if (!dataByName.has(name)) {
        dataByName.set(
          name, {
            labels: [],
            datasets: [
              {
                label: name,
                data: [],
                borderColor: COLORS[colorIndex],
                backgroundColor: COLORS[colorIndex],
              }
            ]
          }
        );
        if (colorIndex === COLORS.length - 1) {
          colorIndex = 0;
        } else {
          colorIndex++;
        }
      }
      let chartData = dataByName.get(name);
      if (chartData !== undefined) {
        let sortedByRootId = Object.entries(byRootId).sort(([rootIdA, valuesA], [rootIdB, valuesB]) => {
          if (valuesA[0][1] > valuesB[0][1]) return 1;
          else return -1;
        });
        sortedByRootId.forEach(([rootId, values]) => {
          values.forEach(([value, time, label]) => {
            chartData?.labels?.push(label || rootId.substring(0, 6));
            chartData?.datasets[0].data.push(value);
          });
        });
      }
    });

    return dataByName;
  }, [metrics]);  

  if (error !== undefined) {
    return <Alert severity="error">
      <AlertTitle>There was an error loading metrics.</AlertTitle>
      Please report the following error to the Sematic team: {error.message}
    </Alert>
  }

  // we do not use `loading` because it will become true again every refresh,
  // leading to a full refresh of the graph, instead of just adding the new data points.
  if (graphDataByName === undefined) {
    return <Loading isLoaded={false}/>;
  } else {
    return <Box sx={{p: 5}}>
      <Typography variant="h3" sx={{mb: 5}}>Pipeline Metrics</Typography>
      {
        graphDataByName.size === 0 && (
          <Typography>
            No metrics registered for this pipeline.
            Use <code>sematic.post_pipeline_metric</code> in the body of a Sematic function.
          </Typography>
        )
      }
      {
        graphDataByName.size > 0 && (
          <>{Array.from(graphDataByName).map(([name, graphData], idx) => (
            <Box key={idx} sx={{mt: 10, width: "45%", minWidth: 500, float: "left", px: 3}}>
              <Typography variant="h6">{name}</Typography>
              <Line data={graphData} />
            </Box>
          ))}</>
        )
      }
    </Box>;
  }
}