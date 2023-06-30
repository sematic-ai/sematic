import noop from "lodash/noop";
import { useCallback, useContext, useEffect, useRef } from "react";
import SnackBarContext from "src/context/SnackBarContext";
import { useFetchLatestRun, useRunNavigation } from "src/hooks/runHooks";
import { pipelineSocket } from "@sematic/common/src/sockets";

function usePipelineSocketMonitor(functionPath: string, callbacks?: {
    onCancel?: () => void,
}) {
    const { onCancel = noop } = callbacks || {};
    const { setSnackMessage } = useContext(SnackBarContext);

    const cancelCallback = useCallback((args: { function_path: string }) => {
        if (args.function_path === functionPath) {
            setSnackMessage({ message: "Pipeline run was canceled." });
            onCancel();
        }
    }, [functionPath, onCancel, setSnackMessage]);

    const loadRun = useFetchLatestRun(functionPath);

    const navigate = useRunNavigation();

    const pipelineUpdateCallback = useCallback(async (args: { function_path: string }) => {
        if (args.function_path === functionPath) {
            const run = await loadRun();
            if (run.id !== latestRunId.current) {
                setSnackMessage({
                    message: "New run available.",
                    actionName: "view",
                    autoHide: false,
                    closable: true,
                    onClick: () => navigate(run.id),
                });
            }
        }
    }, [functionPath, loadRun, navigate, setSnackMessage]);

    const latestRunId = useRef<string>();

    useEffect(() => {
        (async () => {
            const run = await loadRun();
            latestRunId.current = run.id;
        })();
    }, [loadRun]);

    useEffect(() => {
        pipelineSocket.on("cancel", cancelCallback);
        return () => {
            pipelineSocket.off("cancel", cancelCallback);
        }
    }, [cancelCallback]);

    useEffect(() => {
        pipelineSocket.on("update", pipelineUpdateCallback);
        return () => {
            pipelineSocket.off("update", pipelineUpdateCallback);
        }
    }, [pipelineUpdateCallback]);

    return <></>;
}

export default usePipelineSocketMonitor;
