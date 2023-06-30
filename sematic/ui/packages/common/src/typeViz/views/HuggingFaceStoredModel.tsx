import { useCallback, useContext, useMemo } from "react";
import { Chip, Tooltip } from "@mui/material";
import { ContentCopy } from "@mui/icons-material";
import SnackBarContext from "@sematic/common/src/context/SnackBarContext";
import { ViewComponentProps} from "src/typeViz/common";


export function HuggingFaceStoredModelShortView() {
    return (<span>🤗 model</span>);
}

export function HuggingFaceStoredModelFullView(props: ViewComponentProps) {
    const { valueSummary } = props;
    const { values } = valueSummary;
    const { setSnackMessage } = useContext(SnackBarContext);

    const copy = useCallback(() => {
        setSnackMessage({ message: "Copied path to model" });
        navigator.clipboard.writeText(values.path);
    }, [values, setSnackMessage]);

    const contents = useMemo(
        () => {
            const modelTypeShortName = getShortName(values.peft_model_type, values.model_type);

            return (
                <Tooltip title={"Copy path to model: " + values.path}>
                    <Chip
                        icon={<ContentCopy />}
                        onClick={copy}
                        sx={{ paddingLeft: 2, paddingRight: 2}}
                        label={"🤗 "+ modelTypeShortName}
                        variant="outlined"
                    />
                </Tooltip>
            );
        }, [values, copy]
    );
    return contents;
}

function getShortName(peftModelType: string | null, modelType: string) {
    const modelTypeToDisplay = peftModelType ? peftModelType : modelType;
    const modelTypePieces = modelTypeToDisplay.split(".");
    const modelTypeShortName = modelTypePieces[modelTypePieces.length - 1];
    return modelTypeShortName;
}
