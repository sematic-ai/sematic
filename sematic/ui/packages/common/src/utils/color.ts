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

export const TAG_COLORS = [
    {
        color: "rgb(65, 36, 84)",
        backgroundColor: "rgb(232, 222, 238)"
    }, // purple
    {
        color: "rgb(24, 51, 71)",
        backgroundColor: "rgb(91, 151, 189)"
    }, // blue
    {
        color: "rgb(93, 23, 21)",
        backgroundColor: "rgb(255, 226, 221)"
    }, // pink
    {
        color: "rgb(93, 23, 21)",
        backgroundColor: "rgba(238, 224, 218)"
    }, // brown
    {
        color: "rgb(64, 44, 27)",
        backgroundColor: "rgb(253, 236, 200)"
    }, // yellow
    {
        color: "rgb(50, 48, 44)",
        backgroundColor: "rgba(227, 226, 224, 0.5)"
    }, // default
    {
        color: "rgb(145, 145, 142)",
        backgroundColor: "rgb(227, 226, 224)"
    }, // gray
    {
        color: "rgb(28, 56, 41)",
        backgroundColor: "rgb(219, 237, 219)"
    }, // green
    {
        color: "rgb(93, 23, 21)",
        backgroundColor: "rgb(225, 111, 100)"
    }, // red
    {
        color: "rgb(73, 41, 14)",
        backgroundColor: "rgb(250, 222, 201)"
    } // orange
];

export function getTagColor(anyNumber: number): typeof TAG_COLORS[0] {
    return TAG_COLORS[anyNumber % TAG_COLORS.length];
}
