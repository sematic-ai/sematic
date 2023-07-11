import React from "react";
import noop from "lodash/noop";

export const PluginsContext = React.createContext<{
    RunTabs: {
        tabs: string[];
        addTab: (tab: string) => void;
    }
}>({RunTabs: {tabs: [], addTab: noop}});

export default PluginsContext;
