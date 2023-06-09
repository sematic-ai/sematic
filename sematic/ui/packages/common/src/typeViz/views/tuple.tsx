import { ValueComponentProps, ViewComponentProps, renderArtifactRow } from "src/typeViz/common";
import { AliasTypeRepr } from "src/types";


export function TupleValueView(props: ValueComponentProps) {
    const { valueSummary } = props;
    return <span>{`${valueSummary["length"]} elements`}</span>;
}

export function TupleElementsView(props: ViewComponentProps) {
    const { valueSummary, typeSerialization } = props;
    const typeParameterization = (typeSerialization.type as AliasTypeRepr)[2].args;

    return <>
        {
            Array.from(valueSummary).map<React.ReactNode>(
                (element, index) => {
                    const newTypeSerialization = {
                        type: typeParameterization[index].type,
                        registry: typeSerialization.registry,
                    }
                    return renderArtifactRow(index.toString(), newTypeSerialization, element);
                })
        }
    </>;
}
