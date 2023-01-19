import Docstring from "../components/Docstring";
import { usePipelinePanelsContext } from "../hooks/pipelineHooks";

export default function DocumentationPanel() {
    const { selectedRun } = usePipelinePanelsContext();
    return <Docstring docstring={selectedRun?.description} />
} 
