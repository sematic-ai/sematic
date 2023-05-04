import styled from '@emotion/styled';
import Chip, { chipClasses } from "@mui/material/Chip";
import { useCallback, useImperativeHandle, forwardRef, useState } from "react";
import { CanceledStateChip, FailedStateChip, RunningStateChip, SuccessStateChip } from "src/component/RunStateChips";
import CollapseableFilterSection from 'src/pages/RunSearch/filters/CollapseableFilterSection';
import theme from "src/theme/new";
import memoize from 'lodash/memoize';
import { ResettableHandle } from 'src/pages/RunSearch/filters/common';

const StyledChip = styled(Chip)`
    padding-left: ${theme.spacing(1)};
    border-width: 1px;
    border-style: solid;

    & .${chipClasses.label} {
        padding-left: ${theme.spacing(2)};
    }

    &.${chipClasses.filled} {
        svg {
            color: ${theme.palette.common.white};
        }
    }
`;

const Container = styled.div`
    display: flex;
    flex-direction: row;
    flex-wrap: wrap;
    column-gap: ${theme.spacing(2)};
    row-gap: ${theme.spacing(2)};
    margin-bottom: 2px;
`;

interface StatusFilterSectionProps {
    onFiltersChanged?: (filters: string[]) => void;
}

const toogleFilterGenerator = memoize((
    filter: string,
    setFilters: React.Dispatch<React.SetStateAction<Set<string>>>,
    onFiltersChanged: StatusFilterSectionProps['onFiltersChanged']
) =>
    () => useCallback(() => {
        let newFilters: any;
        setFilters((filters) => {
            if (filters.has(filter)) {
                filters.delete(filter);
            } else {
                filters.add(filter);
            }

            newFilters = filters;
            return new Set(filters);
        });

        onFiltersChanged?.(Array.from(newFilters));
    }, []));

const StatusFilterSection = forwardRef<ResettableHandle, StatusFilterSectionProps>((props, ref) => {
    const { onFiltersChanged } = props;
    const [filters, setFilters] = useState<Set<string>>(() => new Set());

    const toggleFilterComplete = toogleFilterGenerator("completed", setFilters, onFiltersChanged!)();
    const toggleFilterFailed = toogleFilterGenerator("failed", setFilters, onFiltersChanged!)();
    const toggleFilterRunning = toogleFilterGenerator("running", setFilters, onFiltersChanged!)();
    const toggleFilterCanceled = toogleFilterGenerator("canceled", setFilters, onFiltersChanged!)();

    useImperativeHandle(ref, () => ({
        reset: () => setFilters(new Set())
    }), []);

    return <CollapseableFilterSection title={"Status"} >
        <Container>
            <StyledChip icon={<SuccessStateChip size={"large"} />}
                variant={filters.has("completed") ? undefined : "outlined"}
                color="success" label={"Completed"} onClick={() => toggleFilterComplete()} />
            <StyledChip icon={<FailedStateChip size={"large"} />}
                variant={filters.has("failed") ? undefined : "outlined"}
                color="error" label={"Failed"} onClick={() => toggleFilterFailed()} />
            <StyledChip icon={<RunningStateChip size={"large"} />}
                variant={filters.has("running") ? undefined : "outlined"}
                color="primary" label={"Running"} onClick={() => toggleFilterRunning()} />
            <StyledChip icon={<CanceledStateChip size={"large"} />}
                variant={filters.has("canceled") ? undefined : "outlined"}
                color="error" label={"Canceled"} onClick={() => toggleFilterCanceled()} />
        </Container>
    </CollapseableFilterSection>;
})

export default StatusFilterSection;
