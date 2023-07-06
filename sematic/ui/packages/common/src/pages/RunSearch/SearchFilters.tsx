import styled from "@emotion/styled";
import Button from "@mui/material/Button";
import { useCallback, useRef } from "react";
import OtherFiltersSection from "src/pages/RunSearch/filters/OtherFilterSection";
import OwnersFilterSection from "src/pages/RunTableCommon/filters/OwnersFilterSection";
import SearchTextSection from "src/pages/RunTableCommon/filters/SearchTextSection";
import StatusFilterSection from "src/pages/RunSearch/filters/StatusFilterSection";
import TagsFilterSection from "src/pages/RunTableCommon/filters/TagsFilterSection";
import { ResettableHandle } from "src/component/common";
import theme from "src/theme/new";
import { AllFilters, FilterType } from "src/pages/RunTableCommon/filters";
import isEmpty from "lodash/isEmpty";
import useEffectOnce from "react-use/lib/useEffectOnce";

const StyledButton = styled(Button)`
    margin: 0 -${theme.spacing(5)};
    height: 50px;
    flex-shrink: 0;
    flex-grow: 0;
    border-radius: 2px;
`;

interface SearchFiltersProps {
    onFiltersChanged: (filters: AllFilters) => void;
}

const SearchFilters = (props: SearchFiltersProps) => {
    const { onFiltersChanged } = props;

    const allFilters = useRef<AllFilters>({});

    const searchTextRef = useRef<ResettableHandle>(null);
    const tagsFiltersRef = useRef<ResettableHandle>(null);
    const statusFiltersRef = useRef<ResettableHandle>(null);
    const ownersFiltersRef = useRef<ResettableHandle>(null);
    const otherFiltersRef = useRef<ResettableHandle>(null);

    const resetAll = useCallback(() => {
        searchTextRef.current?.reset();
        tagsFiltersRef.current?.reset();
        ownersFiltersRef.current?.reset();
        statusFiltersRef.current?.reset();
        otherFiltersRef.current?.reset();

        allFilters.current = {}; 
        onFiltersChanged({});
    }, [onFiltersChanged]);

    const onSearchTextChanged = useCallback((searchText: string) => {
        if (isEmpty(searchText)) {
            delete allFilters.current[FilterType.SEARCH];
        } else {
            allFilters.current[FilterType.SEARCH] = [searchText];
        }
    }, []);

    const onTagsFilterChanged = useCallback((filters: string[]) => {
        if (isEmpty(filters)) {
            delete allFilters.current[FilterType.TAGS];
        } else {
            allFilters.current[FilterType.TAGS] = filters;
        }
    }, []);

    const onStatusFilterChanged = useCallback((filters: string[]) => {
        if (isEmpty(filters)) {
            delete allFilters.current[FilterType.STATUS];
        } else {
            allFilters.current[FilterType.STATUS] = filters;
        }
    }, []);

    const onOwnersFilterChanged = useCallback((filters: string[]) => {
        if (isEmpty(filters)) {
            delete allFilters.current[FilterType.OWNER];
        } else {
            allFilters.current[FilterType.OWNER] = filters;
        }
    }, []);

    const onOtherFilterChanged = useCallback((filters: string[]) => {
        if (isEmpty(filters)) {
            delete allFilters.current[FilterType.OTHER];
        } else {
            allFilters.current[FilterType.OTHER] = filters;
        }
    }, []);

    const applyFilters = useCallback(() => {
        onFiltersChanged({...allFilters.current});
    }, [onFiltersChanged]);

    useEffectOnce(() => {
        if (!isEmpty(allFilters.current)) {
            applyFilters();
        }
    });

    return <>
        <SearchTextSection ref={searchTextRef} onSearchChanged={onSearchTextChanged} />
        <TagsFilterSection ref={tagsFiltersRef} onFiltersChanged={onTagsFilterChanged} />
        <StatusFilterSection ref={statusFiltersRef} onFiltersChanged={onStatusFilterChanged} />
        <OwnersFilterSection ref={ownersFiltersRef} onFiltersChanged={onOwnersFilterChanged} />
        <OtherFiltersSection ref={otherFiltersRef} onFiltersChanged={onOtherFilterChanged} />
        {/* <OrderSection /> disabled for now */}
        <StyledButton variant="contained" disableElevation onClick={applyFilters}>Filter runs</StyledButton>
        <StyledButton variant="contained" disableElevation color={"white"} onClick={resetAll} >
            Clear filters
        </StyledButton>
    </>;
}

export default SearchFilters;
