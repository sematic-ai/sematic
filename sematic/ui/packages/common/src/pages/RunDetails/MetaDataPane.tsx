import { useCallback } from "react";
import { useRunDetailsSelectionContext } from "src/context/RunDetailsSelectionContext";
import GitSection from "src/pages/RunDetails/GitSection";
import PipelineSection from "src/pages/RunDetails/PipelineSection";
import RunSection from "src/pages/RunDetails/RunSection";
import RunTreeSection from "src/pages/RunDetails/RunTreeSection";

const MetaDataPane = () => {
    const { setSelectedPanel } = useRunDetailsSelectionContext();

    return <>
        <PipelineSection onMetricsSectionClicked={useCallback(() => { setSelectedPanel("metrics") }, [setSelectedPanel])} />
        <RunSection />
        <GitSection />
        <RunTreeSection />
    </>;
}

export default MetaDataPane;
