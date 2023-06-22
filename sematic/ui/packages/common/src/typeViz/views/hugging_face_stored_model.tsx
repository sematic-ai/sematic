import { ValueComponentProps, ViewComponentProps} from "src/typeViz/common";

export function HuggingFaceStoredModelShortView(props: ValueComponentProps) {
    return HuggingFaceStoredModelView(props, true);
}

export function HuggingFaceStoredModelFullView(props: ViewComponentProps) {
    return HuggingFaceStoredModelView(props, false);
}

function HuggingFaceStoredModelView(props: ValueComponentProps | ViewComponentProps, short: boolean) {
    const { valueSummary } = props;
    const { values } = valueSummary;
    const modelType = values.peft_model_type ? values.peft_model_type : values.model_type;
    const modelTypePieces = modelType.split(".");
    const modelTypeShortName = modelTypePieces[modelTypePieces.length - 1];
    const contents = (
        short ?
            "model" :
            (<span><strong>{modelTypeShortName}</strong>: {values.path}</span>)
    );

    return (
        <span>🤗 {contents}</span>
    );
  
}
