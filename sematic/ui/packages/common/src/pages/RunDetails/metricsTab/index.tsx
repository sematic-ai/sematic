import MetricsPane from "src/pages/RunDetails/metricsTab/MetricsPane";
import { useContext } from "react";
import { useRunDetailsSelectionContext } from "src/context/RunDetailsSelectionContext";
import LayoutServiceContext from "src/context/LayoutServiceContext";
import useUnmount from "react-use/lib/useUnmount";

export default function RunMetricsPanel() {

    const { selectedRun } = useRunDetailsSelectionContext();
    const { setIsLoading } = useContext(LayoutServiceContext);

    useUnmount(() => {
        setIsLoading(false);
    });

    if (!selectedRun) {
        return null;
    }

    return <MetricsPane run={selectedRun!} setIsLoading={setIsLoading} />;
}
