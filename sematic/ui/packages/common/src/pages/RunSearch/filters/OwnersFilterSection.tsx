import styled from '@emotion/styled';
import Checkbox from '@mui/material/Checkbox';
import { collapseClasses } from '@mui/material/Collapse';
import FormControlLabel from '@mui/material/FormControlLabel';
import FormGroup from '@mui/material/FormGroup';
import { paperClasses } from '@mui/material/Paper';
import { forwardRef, useCallback, useState, useImperativeHandle } from "react";
import CollapseableFilterSection from 'src/pages/RunSearch/filters/CollapseableFilterSection';
import { ResettableHanlde } from 'src/pages/RunSearch/filters/common';
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

const StyledCollapseableFilterSection = styled(CollapseableFilterSection)`
    flex-grow: 0;
    flex-shrink: 1!important;
    
    & .${paperClasses.root} {
        display: flex;
        flex-direction: column;
    }

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

const OwnersFilterSection = forwardRef<ResettableHanlde, OwnersFilterSectionProps>((props, ref) => {
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
            filters.delete('current_user_id');
            newFilters = new Set(filters);
            onFiltersChanged?.(Array.from(newFilters));
            return newFilters;
        });

    }, [onFiltersChanged, setFilters]);

    /***
     * This clears all other filters but the current user filter
     */
    const toogleJustMeFilter = useCallback((checked: boolean) => {
        let newFilters: any;
        setFilters(() => {
            if (checked) {
                newFilters = new Set(['current_user_id']);
            } else {
                newFilters = new Set();
            }
            onFiltersChanged?.(Array.from(newFilters));
            return newFilters;
        });

    }, [onFiltersChanged, setFilters]);

    useImperativeHandle(ref, () => ({
        reset: () => {
            setFilters(new Set());
        }
    }));

    return <StyledCollapseableFilterSection title={"Owner"} >
        <Container>
            <FormGroup>
                <StyledFormControlLabel control={<Checkbox
                    checked={filters.has('current_user_id')}
                    onChange={(e, checked) => toogleJustMeFilter(checked)} />} label="My runs only"
                />
                {['Alice', 'Bob', 'Clark', 'David', 'Edison', 'Frank'].map(
                    (owner) =>
                        <StyledFormControlLabel control={<Checkbox
                            onChange={(e, checked) => toogleFilter(owner, checked)} />} label={owner}
                            checked={filters.has(owner)} />
                )}
            </FormGroup>
        </Container>
    </StyledCollapseableFilterSection>;
})

export default OwnersFilterSection;
