import styled from '@emotion/styled';
import Checkbox from '@mui/material/Checkbox';
import { collapseClasses } from '@mui/material/Collapse';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormGroup from '@mui/material/FormGroup';
import CollapseableFilterSection from 'src/pages/RunSearch/filters/CollapseableFilterSection';
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

interface OwnersFilterSectionProps {
    onFiltersChanged?: (filters: string[]) => void;
}

const OtherFiltersSection = (props: OwnersFilterSectionProps) => {
    return <StyledCollapseableFilterSection title={"Filters"} >
        <Container>
            <FormGroup>
                <StyledFormControlLabel control={<Checkbox defaultChecked />} label="Root runs only" />
            </FormGroup>
        </Container>
    </StyledCollapseableFilterSection>;
}

export default OtherFiltersSection;
