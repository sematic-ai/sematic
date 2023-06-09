import { ValueComponentProps } from "src/typeViz/common";

export default function UnionValue(props: ValueComponentProps) {
    return <code>{JSON.stringify(props.valueSummary)}</code>;
}