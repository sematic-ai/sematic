import { useMemo } from "react";
import { Provider } from "@sematic/react-slot-fill/src";
import PluginsContext from "src/context/pluginsContext";
import useSet from "react-use/lib/useSet";

function PluginsProvider(props: { children: React.ReactNode }) {
    const { children } = props;
    const [tabs, { add }] = useSet<string>();

    const contextValue = useMemo(() => {
        return {
            RunTabs: {
                tabs: Array.from(tabs.values()),
                addTab: add
            }
        }
    }, [tabs, add]);


    return <Provider>
        <PluginsContext.Provider value={contextValue}>
            {children}
        </PluginsContext.Provider>
    </Provider>
}

export default PluginsProvider;