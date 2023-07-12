import { createContext } from "react";
import noop from "lodash/noop";

export enum ArtifactCoordinationState {
    EXPAND_ALL,
    COLLAPSE_ALL,
    DIRTY
}

const ArtifactCoordinationContext = createContext<{
    coordinationState: ArtifactCoordinationState;
    setCoordinationState: (state: ArtifactCoordinationState) => void;
}>({ coordinationState: ArtifactCoordinationState.DIRTY, setCoordinationState: noop});

export default ArtifactCoordinationContext;
