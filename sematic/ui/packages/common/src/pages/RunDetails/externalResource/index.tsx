import ExternalResourcePanelComponent from "@sematic/common/src/pages/RunDetails/externalResource/ExternalResource";
import { useContext } from "react";
import LayoutServiceContext from "src/context/LayoutServiceContext";
import { useRunDetailsSelectionContext } from "src/context/RunDetailsSelectionContext";

export default function ExternalResourcePanel() {
    const { selectedRun } = useRunDetailsSelectionContext();

    const { setIsLoading } = useContext(LayoutServiceContext);

    if (!selectedRun) {
        return null;
    }

    return <ExternalResourcePanelComponent selectedRun={selectedRun} setIsLoading={setIsLoading}/>;
}
