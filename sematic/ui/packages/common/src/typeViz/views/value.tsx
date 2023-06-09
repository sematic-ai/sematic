import { ArtifactExpanderContainer } from "src/typeViz/ArtifactVizTemplate";
import { ValueComponentProps, ViewComponentProps } from "src/typeViz/common";

export default function ValueView(props: ValueComponentProps) {
    const { open } = props;
    return open ? null : (<span>Click to expand</span>);
}

export function ValueExpandedView(props: ViewComponentProps) {
    return <ArtifactExpanderContainer>
        <div style={{ overflow: "auto", maxHeight: "300px" }}>
            <code>{JSON.stringify(props.valueSummary)}</code>
        </div>
    </ArtifactExpanderContainer>
}
