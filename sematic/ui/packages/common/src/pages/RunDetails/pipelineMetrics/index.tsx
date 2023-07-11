import { useContext } from "react";
import LayoutServiceContext from "src/context/LayoutServiceContext";
import { useRootRunContext } from "src/context/RootRunContext";
import BasicMetricsPanel from "src/pages/RunDetails/pipelineMetrics/BasicMetricsPanel";
import useUnmount from "react-use/lib/useUnmount";
import styled from "@emotion/styled";


const ScrollContainerWrapper = styled.div`
    overflow-y: auto;
    margin-right: -25px;
    height: 100%;
`;

function PipelineMetrics() {
    const { rootRun } = useRootRunContext();

    const { setIsLoading } = useContext(LayoutServiceContext);

    useUnmount(() => {
        setIsLoading(false);
    });

    if (!rootRun) {
        return null;
    }

    return <ScrollContainerWrapper>
        <BasicMetricsPanel runId={rootRun.id} functionPath={rootRun.function_path}
            setIsLoading={setIsLoading} />
    </ScrollContainerWrapper>;

}


export default PipelineMetrics;