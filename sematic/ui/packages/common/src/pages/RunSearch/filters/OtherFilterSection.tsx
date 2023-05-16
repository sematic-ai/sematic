import styled from "@emotion/styled";
import Checkbox from "@mui/material/Checkbox";
import { collapseClasses } from "@mui/material/Collapse";
import FormControlLabel from "@mui/material/FormControlLabel";
import FormGroup from "@mui/material/FormGroup";
import { forwardRef, useState, useImperativeHandle, useCallback } from "react";
import { ResettableHandle } from "src/component/common";
import CollapseableFilterSection from "src/pages/RunSearch/filters/CollapseableFilterSection";
import theme from "src/theme/new";

const Container = styled.div`
    margin-top: -${theme.spacing(2)};
    margin-bottom: -${theme.spacing(2.4)};
`;

const StyledCollapseableFilterSection = styled(CollapseableFilterSection)`
    & .${collapseClasses.root} {
        flex-grow: 0;
        flex-shrink: 1;
        overflow-y: auto;
        margin: 0 -${theme.spacing(5)};
    }
`;

const StyledFormControlLabel = styled(FormControlLabel)`
    height: 50px;
    margin-left: ${theme.spacing(2.9)};
`;

interface OtherFilterSectionProps {
    onFiltersChanged?: (filters: string[]) => void;
}

const OtherFiltersSection = forwardRef<ResettableHandle, OtherFilterSectionProps>((props, ref) => {
    const { onFiltersChanged } = props;
    const [rootRunsOnly, setRootRunsOnly] = useState<boolean>(false);

    useImperativeHandle(ref, () => ({
        reset: () => {
            setRootRunsOnly(false);
        }
    }));

    const onRootRunsOnlyChanged = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
        const checked = event.target.checked;
        setRootRunsOnly(checked);
        onFiltersChanged?.(checked ? ["rootRunsOnly"] : []);
    }, [setRootRunsOnly, onFiltersChanged]);


    return <StyledCollapseableFilterSection title={"Filters"} >
        <Container>
            <FormGroup>
                <StyledFormControlLabel control={
                    <Checkbox checked={rootRunsOnly} onChange={onRootRunsOnlyChanged} />} label="Root runs only" />
            </FormGroup>
        </Container>
    </StyledCollapseableFilterSection>;
});

export default OtherFiltersSection;
