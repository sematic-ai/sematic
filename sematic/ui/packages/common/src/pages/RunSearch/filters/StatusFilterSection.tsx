import styled from "@emotion/styled";
import Chip, { chipClasses } from "@mui/material/Chip";
import { forwardRef, useCallback, useImperativeHandle, useState } from "react";
import { CanceledStateChip, FailedStateChip, RunningStateChip, SuccessStateChip } from "src/component/RunStateChips";
import { ResettableHandle } from "src/component/common";
import CollapseableFilterSection from "src/pages/RunSearch/filters/CollapseableFilterSection";
import { StatusFilters } from "src/pages/RunTableCommon/filters";
import theme from "src/theme/new";

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

const useToogleFilterCallbackGenerator = (
    filter: StatusFilters,
    setFilters: React.Dispatch<React.SetStateAction<Set<string>>>,
    onFiltersChanged: StatusFilterSectionProps["onFiltersChanged"]) =>
    useCallback(() => {
        let newFilters: any;
        setFilters((filters) => {
            if (filters.has(filter)) {
                filters.delete(filter);
            } else {
                filters.add(filter);
            }

            newFilters = filters;
            onFiltersChanged?.(Array.from(newFilters));
            return new Set(filters);
        });
    }, [filter, setFilters, onFiltersChanged]);

const StatusFilterSection = forwardRef<ResettableHandle, StatusFilterSectionProps>((props, ref) => {
    const { onFiltersChanged } = props;
    const [filters, setFilters] = useState<Set<string>>(() => new Set());

    const toggleFilterComplete = useToogleFilterCallbackGenerator("completed", setFilters, onFiltersChanged!);
    const toggleFilterFailed = useToogleFilterCallbackGenerator("failed", setFilters, onFiltersChanged!);
    const toggleFilterRunning = useToogleFilterCallbackGenerator("running", setFilters, onFiltersChanged!);
    const toggleFilterCanceled = useToogleFilterCallbackGenerator("canceled", setFilters, onFiltersChanged!);

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
