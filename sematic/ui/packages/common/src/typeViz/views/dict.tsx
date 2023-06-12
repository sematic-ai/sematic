
import { ValueComponentProps, ViewComponentProps, renderArtifactRow } from "src/typeViz/common";
import { AliasTypeRepr } from "src/types";

export default function DictValueView(props: ValueComponentProps) {
    const { valueSummary } = props;
    return <span>{`${Array.from(valueSummary).length} entries`}</span>;
}

export function DictElementsView(props: ViewComponentProps) {
    const { valueSummary, typeSerialization } = props;
    const typeParameterization = (typeSerialization.type as AliasTypeRepr)[2].args;

    return <>
        {
            Array.from(valueSummary as [any, any]).map<React.ReactNode>(
                (pair, index) => {
                    const newTypeSerialization = {
                        type: typeParameterization[1].type,
                        registry: typeSerialization.registry,
                    }
                    return renderArtifactRow(pair[0].toString(), newTypeSerialization, pair[1]);
                })
        }
    </>;
}
