import styled from '@emotion/styled';
import { useState } from 'react';
import TagsInput from "src/component/TagsInput";
import { ScrollableCollapseableFilterSection } from 'src/pages/RunSearch/filters/CollapseableFilterSection';
import theme from "src/theme/new";

const Container = styled.div`
    margin: -${theme.spacing(2.4)} 0;
    min-height: 50px;
    flex-direction: column;
    justify-content: center;
    display: flex;
    padding-left: ${theme.spacing(5)};
    padding-right: ${theme.spacing(5)};
    padding-bottom: ${theme.spacing(1)};
`;

const StyledScrollableSection = styled(ScrollableCollapseableFilterSection) <{
    expanded: boolean;
}>`
    justify-content: start;
    min-height: ${({ expanded }) => expanded ? 100 : 50}px;
    transition: min-height 300ms cubic-bezier(0.4, 0, 0.2, 1) 0ms;
`;


const TagsFilterSection = () => {
    const [expanded, setExpanded] = useState(false);

    return <StyledScrollableSection title={"Tags"} expanded={expanded}
        onChange={(_, expanded) => setExpanded(expanded)}>
        <Container>
            <TagsInput />
        </Container>
    </StyledScrollableSection>;
}

export default TagsFilterSection;
