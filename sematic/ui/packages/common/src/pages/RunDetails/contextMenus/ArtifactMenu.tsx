import { useCallback, useContext, useMemo } from "react";
import ContextMenu from "src/component/ContextMenu";
import SnackBarContext from "src/context/SnackBarContext";

const ANCHOR_OFFSET = {x: 13, y: -11};

interface ArtifactMenuProps {
    anchorEl: HTMLElement | null;
    artifactId: string;
}

function ArtifactMenu(props: ArtifactMenuProps) {
    const { anchorEl, artifactId } = props;
    const { setSnackMessage } = useContext(SnackBarContext);

    const onCopyArtifactID = useCallback(() => {
        navigator.clipboard.writeText(artifactId);
        setSnackMessage({ message: "Artifact ID copied" });
    }, [setSnackMessage, artifactId]);

    const commands = useMemo(() => {
        return [
            {
                title: "Copy artifact ID",
                onClick: onCopyArtifactID
            }
        ]
    }, [onCopyArtifactID]);

    return <ContextMenu anchorEl={anchorEl} commands={commands} anchorOffset={ANCHOR_OFFSET} />;
}

export default ArtifactMenu;
