import { CommonValueViewProps } from "./common";

export default function HuggingFaceStoredModelView(props: CommonValueViewProps) {
    const { valueSummary } = props;
    const { values } = valueSummary;
    const modelType = values.peft_model_type ? values.peft_model_type : values.model_type;
    const modelTypePieces = modelType.split(".");
    const modelTypeShortName = modelTypePieces[modelTypePieces.length - 1];

    return (
        <span>🤗 <strong>{modelTypeShortName}</strong>: {values.path}</span>
    );
}

