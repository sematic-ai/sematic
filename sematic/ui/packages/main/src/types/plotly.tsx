import { CommonValueViewProps } from "./common";
import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-cartesian-dist";

const Plot = createPlotlyComponent(Plotly);

export default function PlotlyFigureValueView(props: CommonValueViewProps) {
    let { valueSummary } = props;
    let { data, layout, config } = valueSummary["figure"];
    return <Plot data={data} layout={layout} config={config} />;
}