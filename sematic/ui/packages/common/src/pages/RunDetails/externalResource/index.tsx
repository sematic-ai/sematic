import ExternalResourcePanelComponent from "@sematic/common/src/pages/RunDetails/externalResource/ExternalResource";
import { useContext } from "react";
import LayoutServiceContext from "src/context/LayoutServiceContext";
import { useRunDetailsSelectionContext } from "src/context/RunDetailsSelectionContext";
import useUnmount from "react-use/lib/useUnmount";

export default function ExternalResourcePanel() {
    const { selectedRun } = useRunDetailsSelectionContext();

    const { setIsLoading } = useContext(LayoutServiceContext);

    useUnmount(() => {
        setIsLoading(false);
    });

    if (!selectedRun) {
        return null;
    }

    return <ExternalResourcePanelComponent selectedRun={selectedRun} setIsLoading={setIsLoading}/>;
}
