import { Alert, AlertTitle, Box, Typography } from '@mui/material';
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
import { useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import Loading from 'src/components/Loading';
import useFetchRunMetrics from 'src/hooks/metricsHooks';
import { usePipelinePanelsContext } from 'src/hooks/pipelineHooks';

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

export default function RunMetricsPanel() {
  const { selectedRun } = usePipelinePanelsContext();

  const [ payload, loading, error ] = useFetchRunMetrics(selectedRun!.id);

  const metrics = useMemo(() => {
    return payload?.content;
  }, [payload]);

  const graphDataByName = useMemo(() => {
    if (metrics === undefined) {
      return undefined;
    }
    let dataByName: Map<string, ChartData<"line", number[], string>> = new Map();
    let colorIndex = 0;
    Object.entries(metrics).forEach((value) => {
      let [ name, byRootId ] = value;
      if (!dataByName.has(name)) {
        dataByName.set(
          name, {
            labels: [],
            datasets: [
              {
                label: name,
                data: [],
                borderColor: COLORS[colorIndex],
                backgroundColor: COLORS[colorIndex]
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
      let values = Object.entries(byRootId)[0][1];
      let chartData = dataByName.get(name);
      if (chartData !== undefined) {
        values.forEach(([value, time, label]) => {
          chartData?.labels?.push(label || new Date(time).toLocaleString());
          chartData?.datasets[0].data.push(value);
        })
      }
    })
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
  if (graphDataByName == undefined) {
    return <Loading isLoaded={false}/>;
  } else {
    if (graphDataByName.size === 0) {
      return <Typography>
        No metrics registered for this run.
        Use <code>sematic.post_run_metric</code> in the body of a Sematic function.
        </Typography>;
    } else {
      return <>{Array.from(graphDataByName).map(([name, graphData], idx) => (
        <Box key={idx} sx={{mt: 5, width: "50%", minWidth: 500}}>
          <Typography variant="h6">{name}</Typography>
          <Line data={graphData} />
        </Box>
      ))}</>
    }
  }
  return <>abc</>;
}