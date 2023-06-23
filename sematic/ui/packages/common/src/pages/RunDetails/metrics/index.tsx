import MetricsPane from "src/pages/RunDetails/metrics/MetricsPane";
import { useContext } from "react";
import { useRunDetailsSelectionContext } from "src/context/RunDetailsSelectionContext";
import LayoutServiceContext from "src/context/LayoutServiceContext";

export default function RunMetricsPanel() {

    const { selectedRun } = useRunDetailsSelectionContext();
    const { setIsLoading } = useContext(LayoutServiceContext);

    if (!selectedRun) {
        return null;
    }

    return <MetricsPane run={selectedRun!} setIsLoading={setIsLoading} />;
}
