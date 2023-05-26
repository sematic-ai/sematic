import { Alert } from "@mui/material";
import { AnyTypeSerialization, DataclassTypeRepr } from "@sematic/common/src/types";
import { ValueComponentProps, ViewComponentProps, renderArtifactRow } from "src/typeViz/common";

export default function DataclassValueView(props: ValueComponentProps) {
    let valueSummary: {
        values: { [name: string]: any };
        types: { [name: string]: AnyTypeSerialization };
    } = props.valueSummary;

    let typeRepr = props.typeSerialization.type as DataclassTypeRepr;
    let typeFields = typeRepr[2].fields;
    if (typeFields === undefined) {
        return <Alert severity="error">Incorrect type serialization</Alert>;
    }

    const fieldsToShow = valueSummary.values || valueSummary;

    return <span>{Object.entries(fieldsToShow).length} fields</span>;
}


export function DataclassElementsView(props: ViewComponentProps) {
    const { typeSerialization } = props;
    let valueSummary: {
        values: { [name: string]: any };
        types: { [name: string]: AnyTypeSerialization };
    } = props.valueSummary;
    const typeParameterization = (typeSerialization.type as DataclassTypeRepr)[2];
    let typeFields = typeParameterization.fields;

    const fieldsToShow = valueSummary.values || valueSummary;

    return <>
        {
            Object.entries(fieldsToShow).map<React.ReactNode>(
                ([name, fieldSummary]) => {
                    const newTypeSerialization = {
                        type: valueSummary.types?.[name]?.type || typeFields[name]?.type,
                        registry: typeSerialization.registry,
                    }
                    return renderArtifactRow(name, newTypeSerialization, fieldSummary);
                })
        }
    </>
}
