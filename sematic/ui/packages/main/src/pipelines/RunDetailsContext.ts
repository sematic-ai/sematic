import React from "react";

const RunPanelContext = React.createContext<{
    setFooterRenderProp: (renderProp: (() => JSX.Element) | null) => void;
    scrollerId: string;
    scrollContainerRef: React.MutableRefObject<HTMLElement | undefined>;
    setIsLoading: (isLoading: boolean) => void;
} | null>(null);

export default RunPanelContext;
