import { useCallback, useContext, useMemo } from "react";
import ContextMenu from "src/component/ContextMenu";
import SnackBarContext from "src/context/SnackBarContext";
import ArtifactCoordinationContext, { ArtifactCoordinationState } from "src/context/artifactCoordinationContext";

const ANCHOR_OFFSET = {x: 13, y: -11};

interface ArtifactMenuProps {
    anchorEl: HTMLElement | null;
    artifactId: string;
}

function ArtifactMenu(props: ArtifactMenuProps) {
    const { anchorEl, artifactId } = props;
    const { setSnackMessage } = useContext(SnackBarContext);
    
    const { coordinationState, setCoordinationState } = useContext(ArtifactCoordinationContext);

    const onCopyArtifactID = useCallback(() => {
        navigator.clipboard.writeText(artifactId);
        setSnackMessage({ message: "Artifact ID copied" });
    }, [setSnackMessage, artifactId]);

    const commands = useMemo(() => {
        return [
            {
                title: "Copy artifact ID",
                onClick: onCopyArtifactID
            },
            {
                title: "Expand all",
                onClick: () => setCoordinationState(ArtifactCoordinationState.EXPAND_ALL),
                disabled: coordinationState === ArtifactCoordinationState.EXPAND_ALL
            },
            {
                title: "Collapse all",
                onClick: () => setCoordinationState(ArtifactCoordinationState.COLLAPSE_ALL),
                disabled: coordinationState === ArtifactCoordinationState.COLLAPSE_ALL
            }
        ]
    }, [coordinationState, onCopyArtifactID, setCoordinationState]);

    return <ContextMenu anchorEl={anchorEl} commands={commands} anchorOffset={ANCHOR_OFFSET} />;
}

export default ArtifactMenu;
