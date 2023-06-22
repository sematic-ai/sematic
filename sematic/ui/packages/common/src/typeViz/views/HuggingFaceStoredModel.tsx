import { useMemo } from "react";
import { ValueComponentProps, ViewComponentProps} from "src/typeViz/common";


interface HuggingFaceStoredModelViewProps extends ValueComponentProps { short: boolean }

export function HuggingFaceStoredModelShortView(props: ValueComponentProps) {
    return <HuggingFaceStoredModelView {...props} short={true} />;
}

export function HuggingFaceStoredModelFullView(props: ViewComponentProps) {
    return <HuggingFaceStoredModelView {...props} short={false} />;
}

function HuggingFaceStoredModelView(props: HuggingFaceStoredModelViewProps) {
    const { valueSummary, short } = props;
    const { values } = valueSummary;
    const contents = useMemo(
        () => {
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
        }, [values, short]
    );
    return contents;
}
