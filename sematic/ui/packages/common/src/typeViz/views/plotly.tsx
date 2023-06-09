
import createPlotlyComponent from "react-plotly.js/factory";
import { ArtifactExpanderContainer } from "src/typeViz/ArtifactVizTemplate";
import { ValueComponentProps, ViewComponentProps } from "src/typeViz/common";

const Plotly = require("plotly.js-cartesian-dist");

const Plot = createPlotlyComponent(Plotly);

export default function PlotlyFigureValueView(props: ValueComponentProps) {
    let { open } = props;

    if (open) {
        return null
    }
    return <span>View figure</span>;
    
}


export function PlotlyFigureExpandedView(props: ViewComponentProps) {
    let { valueSummary } = props;

    let { data, layout, config } = valueSummary["figure"];
    return <ArtifactExpanderContainer>
        <Plot data={data} layout={layout} config={config} />
    </ArtifactExpanderContainer>;
}
