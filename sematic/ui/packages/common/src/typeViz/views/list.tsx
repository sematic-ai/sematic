import { useMemo } from "react";
import { ArtifactInfoContainer } from "src/typeViz/ArtifactVizTemplate";
import { ValueComponentProps, ViewComponentProps, renderArtifactRow } from "src/typeViz/common";
import { AliasTypeRepr } from "src/types";

export default function ListValueView(props: ValueComponentProps) {
    const { valueSummary } = props;
    return <span>{`${valueSummary["length"]} elements`}</span>;
}

export function ListElementsView(props: ViewComponentProps) {
    const { valueSummary, typeSerialization } = props;

    const typeParameterization = (typeSerialization.type as AliasTypeRepr)[2].args;

    const infoSection = useMemo(() => {
        const diff = valueSummary["length"] - valueSummary["summary"].length;
        if (diff <= 0) return null;
        return <ArtifactInfoContainer>
            and {diff} more item{diff === 1 ?  "" : "s"}.
        </ArtifactInfoContainer>
    }, [valueSummary])

    return <>
        {Array.from(valueSummary["summary"]).map<React.ReactNode>(
            (element, index) => {
                const newTypeSerialization = {
                    type: typeParameterization[0].type,
                    registry: typeSerialization.registry,
                }
                return renderArtifactRow(index.toString(), newTypeSerialization, element);
            })}
        {infoSection}
    </>;
}
