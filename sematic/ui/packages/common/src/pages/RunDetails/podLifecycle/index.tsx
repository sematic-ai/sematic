import PodLifecycleComponent from "src/pages/RunDetails/podLifecycle/PodLifecycle";
import { useContext } from "react";
import LayoutServiceContext from "src/context/LayoutServiceContext";
import { useRunDetailsSelectionContext } from "src/context/RunDetailsSelectionContext";
import styled from "@emotion/styled";
import { accordionDetailsClasses} from "@mui/material/AccordionDetails";
import theme from "src/theme/new";
import useUnmount from "react-use/lib/useUnmount";

const StyledPodLifecycleComponent = styled(PodLifecycleComponent)`
    & .${accordionDetailsClasses.root} {
        border-bottom: 1px solid ${theme.palette.p3border.main};
    }
`;

export default function PodLifecyclePanel() {
    const { selectedRun } = useRunDetailsSelectionContext();
    const { setIsLoading } = useContext(LayoutServiceContext);

    useUnmount(() => {
        setIsLoading(false);
    });

    if (!selectedRun) {
        return null;
    }

    return <StyledPodLifecycleComponent key={selectedRun!.id} runId={selectedRun!.id} setIsLoading={setIsLoading}/>
}
