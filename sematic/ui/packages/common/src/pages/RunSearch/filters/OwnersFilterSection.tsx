import styled from '@emotion/styled';
import Checkbox from '@mui/material/Checkbox';
import { collapseClasses } from '@mui/material/Collapse';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormGroup from '@mui/material/FormGroup';
import { forwardRef, useCallback, useImperativeHandle, useState } from "react";
import { ScrollableCollapseableFilterSection } from 'src/pages/RunSearch/filters/CollapseableFilterSection';
import { ResettableHandle } from 'src/pages/RunSearch/filters/common';
import theme from "src/theme/new";


const Container = styled.div`
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    column-gap: ${theme.spacing(2)};
    row-gap: ${theme.spacing(2)};
    margin-top: -${theme.spacing(2)};
    margin-bottom: 2px;

    overflow-y: auto;
`;

const StyledFormControlLabel = styled(FormControlLabel)`
    height: 50px;
    margin-left: ${theme.spacing(2.9)};
`;

interface OwnersFilterSectionProps {
    onFiltersChanged?: (filters: string[]) => void;
}

const OwnersFilterSection = forwardRef<ResettableHandle, OwnersFilterSectionProps>((props, ref) => {
    const { onFiltersChanged } = props;
    const [filters, setFilters] = useState<Set<string>>(() => new Set());

    const toogleFilter = useCallback((filter: string, checked: boolean) => {
        let newFilters: any;
        setFilters((filters) => {
            if (checked) {
                filters.add(filter);
            } else {
                filters.delete(filter);
            }
            newFilters = new Set(filters);
            onFiltersChanged?.(Array.from(newFilters));
            return newFilters;
        });

    }, [onFiltersChanged, setFilters]);

    useImperativeHandle(ref, () => ({
        reset: () => {
            setFilters(new Set());
        }
    }));

    return <ScrollableCollapseableFilterSection title={"Owner"} >
        <Container>
            <FormGroup>
                <StyledFormControlLabel control={<Checkbox
                    checked={filters.has('current_user_id')}
                    onChange={(e, checked) => toogleFilter("current_user_id", checked)} />} label="Your runs"
                />
                {['Alice', 'Bob', 'Clark', 'David', 'Edison', 'Frank'].map(
                    (owner, index) =>
                        <StyledFormControlLabel key={index} control={<Checkbox
                            onChange={(e, checked) => toogleFilter(owner, checked)} />} label={owner}
                            checked={filters.has(owner)} />
                )}
            </FormGroup>
        </Container>
    </ScrollableCollapseableFilterSection>;
})

export default OwnersFilterSection;
