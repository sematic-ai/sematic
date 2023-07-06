import SourceCodeComponent from "@sematic/common/src/pages/RunDetails/sourcecode/SourceCode";
import { usePipelinePanelsContext } from "../hooks/pipelineHooks";

function SourceCode() {
    const { selectedRun } = usePipelinePanelsContext();

    return <SourceCodeComponent run={selectedRun!} />;
}

export default SourceCode;
