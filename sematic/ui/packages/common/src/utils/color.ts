const CHART_COLORS = [
    "rgb(255, 99, 132)",
    "rgb(54, 162, 235)",
    "rgb(255, 206, 86)",
    "rgb(75, 192, 192)",
    "rgb(153, 102, 255)",
    "rgb(255, 159, 64)",
];

export function getChartColor(index: number): string {
    return CHART_COLORS[index % CHART_COLORS.length];
}
