import { useContext } from "react";
import LayoutServiceContext from "src/context/LayoutServiceContext";
import { useRootRunContext } from "src/context/RootRunContext";
import BasicMetricsPanel from "src/pages/RunDetails/pipelineMetrics/BasicMetricsPanel";
import useUnmount from "react-use/lib/useUnmount";

function PipelineMetrics() {
    const { rootRun } = useRootRunContext();

    const { setIsLoading } = useContext(LayoutServiceContext);

    useUnmount(() => {
        setIsLoading(false);
    });

    if (!rootRun ) {
        return null;
    }

    return <BasicMetricsPanel runId={rootRun.id} functionPath={rootRun.function_path}
        setIsLoading={setIsLoading} />
        
}


export default PipelineMetrics;