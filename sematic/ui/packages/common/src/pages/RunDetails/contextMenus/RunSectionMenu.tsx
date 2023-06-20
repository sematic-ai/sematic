import { useContext, useMemo, useCallback } from "react";
import ContextMenu from "src/component/ContextMenu";
import { useRootRunContext } from "src/context/RootRunContext";
import SnackBarContext from "src/context/SnackBarContext";
import { useCancelRun, useRerun } from "src/hooks/resolutionHooks";

const ANCHOR_OFFSET = {x: 13, y: -38};

interface RunSectionActionMenuProps {
    anchorEl: HTMLElement | null;
}

function RunSectionActionMenu(props: RunSectionActionMenuProps) {
    const { anchorEl } = props;

    const { rootRun, resolution } = useRootRunContext();

    const { setSnackMessage } = useContext(SnackBarContext);

    const [rerunState, rerun] = useRerun(rootRun!.id, rootRun!.id);
    const [cancelRunState, cancel] = useCancelRun(rootRun!.id);

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
        () => !!resolution?.container_image_uri && !rerunState.loading,
        [resolution, rerunState]
    );

    const onCopyShareClick = useCallback(() => {
        navigator.clipboard.writeText(window.location.href);
        setSnackMessage({ message: "Resolution link copied" });
    }, [setSnackMessage]);

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
            }
        ]
    }, [setSnackMessage, rerun, cancel, onCopyShareClick, rerunEnable, cancelEnabled]);

    return <ContextMenu anchorEl={anchorEl} commands={commands} anchorOffset={ANCHOR_OFFSET} />;
}

export default RunSectionActionMenu;
