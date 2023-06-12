import { ArtifactExpanderContainer } from "src/typeViz/ArtifactVizTemplate";
import { ValueComponentProps, ViewComponentProps } from "src/typeViz/common";

export function ReprValuePresentation({ value }: {
    value: string;
}) {
    return <pre>{value}</pre>;
}

export function ReprValueView(props: ValueComponentProps) {
    if (!props.open) {
        return <span>Click to expand</span>;
    }
    return null;
};

export function ReprExpandedView(props: ViewComponentProps) {
    return <ArtifactExpanderContainer>
        <ReprValuePresentation value={props.valueSummary["repr"]} />
    </ArtifactExpanderContainer>;
};
