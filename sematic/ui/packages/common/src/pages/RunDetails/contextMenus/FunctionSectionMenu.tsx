import { useCallback, useContext, useMemo } from "react";
import ContextMenu from "src/component/ContextMenu";
import { useRootRunContext } from "src/context/RootRunContext";
import { useRunDetailsSelectionContext } from "src/context/RunDetailsSelectionContext";
import SnackBarContext from "src/context/SnackBarContext";
import { useCancelRun, useRerun } from "src/hooks/resolutionHooks";

const ANCHOR_OFFSET = {x: 13, y: -11};

interface FunctionSectionActionMenuProps {
    anchorEl: HTMLElement | null;
}

function FunctionSectionActionMenu(props: FunctionSectionActionMenuProps) {
    const { anchorEl } = props;

    const { rootRun, resolution, graph } = useRootRunContext();
    const { selectedRun  } = useRunDetailsSelectionContext();

    const { setSnackMessage } = useContext(SnackBarContext);

    const [rerunState, rerun] = useRerun(rootRun?.id, selectedRun?.id);
    const [cancelRunState, cancel] = useCancelRun(rootRun!.id);

    const selectedRunInputEdges = useMemo(
        () => graph?.edges.filter((edge) => edge.destination_run_id === selectedRun?.id),
        [graph, selectedRun?.id]
    );

    const cancelEnabled = useMemo(
        () => {
            if (!rootRun) {
                return false;
            }
            if (cancelRunState.loading) {
                return false;
            }
            return !["FAILED", "NESTED_FAILED", "RESOLVED", "CANCELED"].includes(
                rootRun!.future_state
            );
        }, [rootRun, cancelRunState]
    );

    const rerunEnable = useMemo(
        () => selectedRunInputEdges?.every((edge) => !!edge.artifact_id)
            && !!resolution?.container_image_uri && !rerunState.loading,
        [resolution, rerunState, selectedRunInputEdges]
    );

    const onCopyShareClick = useCallback(() => {
        navigator.clipboard.writeText(window.location.href);
        setSnackMessage({ message: "Resolution link copied" });
    }, [setSnackMessage]);

    const onCopyRunIdClick = useCallback(() => {
        navigator.clipboard.writeText(selectedRun?.id || "");
        setSnackMessage({ message: "Resolution link copied" });
    }, [setSnackMessage, selectedRun]);

    const commands = useMemo(() => {
        return [
            {
                title: "Rerun",
                disabled: !rerunEnable,
                onClick: async () => {
                    try {
                        rerun();
                    } catch (error) {
                        setSnackMessage({ message: "Failed to trigger rerun." });
                    }
                }
            },
            {
                title: "Cancel",
                disabled: !cancelEnabled,
                onClick: () => {
                    try {
                        cancel();
                    } catch (error) {
                        setSnackMessage({ message: "Failed to cancel pipeline run." });
                    }
                }
            },
            {
                title: "Share",
                onClick: onCopyShareClick
            },
            {
                title: "Copy run ID",
                onClick: onCopyRunIdClick
            }
        ]
    }, [setSnackMessage, rerun, cancel, onCopyShareClick, onCopyRunIdClick, rerunEnable, cancelEnabled]);

    return <ContextMenu anchorEl={anchorEl} commands={commands} anchorOffset={ANCHOR_OFFSET} />;
}

export default FunctionSectionActionMenu;
