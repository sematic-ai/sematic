import OtherFiltersSection from 'src/pages/RunSearch/filters/OtherFilterSection';
import OwnersFilterSection from 'src/pages/RunSearch/filters/OwnersFilterSection';
import SearchTextSection from 'src/pages/RunSearch/filters/SearchTextSection';
import StatusFilterSection from 'src/pages/RunSearch/filters/StatusFilterSection';
import TagsFilterSection from 'src/pages/RunSearch/filters/TagsFilterSection';
import Button from '@mui/material/Button';
import styled from '@emotion/styled';
import theme from 'src/theme/new';

const StyledButton = styled(Button)`
    margin: 0 -${theme.spacing(5)};
    height: 50px;
    flex-shrink: 0;
    flex-grow: 0;
`;

const SearchFilters = () => {
    return <>
        <SearchTextSection />
        <TagsFilterSection />
        <StatusFilterSection />
        <OwnersFilterSection />
        <OtherFiltersSection />
        {/* <OrderSection /> disabled for now */}
        <StyledButton variant="contained" disableElevation>Filter runs</StyledButton>
        <StyledButton variant="contained" disableElevation color={"white"}>Clear filters</StyledButton>
    </>;
}

export default SearchFilters;
