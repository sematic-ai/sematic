import { ValueComponentProps, ViewComponentProps} from "src/typeViz/common";

export default function PromptResponseCollapsedView(props: ValueComponentProps) {
    return <span>view prompt & response</span>;
}

export function PromptResponseExpandedView(props: ViewComponentProps) {
    let { valueSummary } = props;
    let { values } = valueSummary;
    const prompt = values.prompt;
    const response = values.response;
    const promptJsx = prompt.split("\n").map((str: string) => <p>{str}</p>);
    const responseJsx = response.split("\n").map((str: string) => <p>{str}</p>);

    return (
        <div>
            <div>
                <span><strong>Prompt</strong></span>
                <div>{promptJsx}</div>
            </div>
            <div>
                <span><strong>Response</strong></span>
                <div>{responseJsx}</div>
            </div>
        </div>
    );
}
