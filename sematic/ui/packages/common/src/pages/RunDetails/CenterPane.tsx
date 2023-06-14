import { useRunDetailsSelectionContext } from "src/context/RunDetailsSelectionContext";
import FunctionSection from "src/pages/RunDetails/FunctionSection";
import RunTabs from "src/pages/RunDetails/RunTabs";
import { useMemo } from "react";
import ReactFlowDag from "src/pages/RunDetails/dag/ReactFlowDag";

const CenterPane = () => {
    const { selectedPanel } = useRunDetailsSelectionContext();

    return useMemo(() => {
        if (selectedPanel === "dag") {
            return <ReactFlowDag />;
        }
        return <>
            <FunctionSection />
            <RunTabs />
        </>;
    }, [selectedPanel]);
}

export default CenterPane;
