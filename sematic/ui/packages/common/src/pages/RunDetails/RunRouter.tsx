import { useAtom } from "jotai";
import { useEffect } from "react";
import { useParams } from "react-router-dom";
import Loading from "src/component/Loading";
import Alert from "@mui/material/Alert";
import { useRunNavigation, selectedRunHashAtom, useFetchRun } from "src/hooks/runHooks";
import { Run } from "src/Models";

interface RunViewPresentationProps {
    rootRun: Run;
}
export function createRunRouter(
    PresentationComponent: React.ComponentClass<RunViewPresentationProps> | React.FunctionComponent<RunViewPresentationProps>) {
    return function RunViewRouter() {
        const { rootId } = useParams();
    
        if (!rootId) {
            throw new Error(
                "`rootId` is expected from the URL. This component might be used with wrong route.");
        }
        const navigate = useRunNavigation();
        const [run, isLoading, error] = useFetchRun(rootId!);
        const [, setSelectedRunId] = useAtom(selectedRunHashAtom);
    
        useEffect(() => {
            if (!run) {
                return;
            }
            if (rootId !== run.root_id) {
                // in case `rootId` is actually a nested run. Navigate to new URL
                const nestedRunId = rootId!;
                navigate(run.root_id, true, { "run": nestedRunId });
            }
        }, [run, rootId, navigate, setSelectedRunId]);
    
        if (isLoading) {
            return <Loading />
        }
    
        if (error) {
            return <Alert severity="error">{error.message}</Alert>
        }
    
        if (rootId !== run!.root_id) {
            // in case `rootId` is actually a nested run. Render nothing. Page
            // will be redirected soon.
            return <></>;
        }
    
        // Otherwise, load `PipelineRunViewPresentation` to actually render root run.
        return <PresentationComponent rootRun={run!} />
    }
}
