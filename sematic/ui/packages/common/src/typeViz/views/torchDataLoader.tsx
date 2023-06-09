import { ArtifactLine } from "src/typeViz/ArtifactVizTemplate";
import { ValueComponentProps, ViewComponentProps, renderArtifactRow } from "src/typeViz/common";
import { BoolValueViewPresentation } from "src/typeViz/views/boolean";

export default function TorchDataLoaderValueView(props: ValueComponentProps) {
    return <span>5 fields</span>;
}

export function TorchDataFieldsView(props: ViewComponentProps) {
    let { valueSummary, typeSerialization } = props;

    return <>
        <ArtifactLine name={"Batch size"}>
            {valueSummary["batch_size"]}
        </ArtifactLine>
        <ArtifactLine name={"Number of suprocesses"}>
            {valueSummary["num_workers"]}
        </ArtifactLine>
        <ArtifactLine name={"Copy tensors into pinned memory"}>
            <BoolValueViewPresentation value={valueSummary["pin_memory"]} />
        </ArtifactLine>
        <ArtifactLine name={"Timeout"}>
            {valueSummary["timeout"]} sec.
        </ArtifactLine>
        {
            renderArtifactRow("Dataset", {
                registry: typeSerialization.registry,
                type: ["builtin", "repr", {}]
            }, valueSummary["dataset"])
        }
    </>
}