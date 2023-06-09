import { ValueComponentProps } from "src/typeViz/common";

export default function StrValueView(props: ValueComponentProps) {
    return (<pre>"{props.valueSummary}"</pre>);
}
