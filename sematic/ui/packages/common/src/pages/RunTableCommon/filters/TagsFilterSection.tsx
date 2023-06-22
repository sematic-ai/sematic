import styled from "@emotion/styled";
import { useState, useRef, forwardRef, useImperativeHandle } from "react";
import TagsInput from "src/component/TagsInput";
import { ResettableHandle } from "src/component/common";
import { ScrollableCollapseableFilterSection } from "src/pages/RunSearch/filters/CollapseableFilterSection";
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

interface TagsFilterSectionProps {
    onFiltersChanged?: (filters: string[]) => void;
}

const TagsFilterSection = forwardRef<ResettableHandle, TagsFilterSectionProps>((props, ref) => {
    const { onFiltersChanged } = props;

    const [expanded, setExpanded] = useState(false);

    const tagInputRef = useRef<ResettableHandle>(null);

    useImperativeHandle(ref, () => ({
        reset: () => {
            tagInputRef.current?.reset();
        }
    }));

    return <StyledScrollableSection title={"Tags"} expanded={expanded}
        onChange={(_, expanded) => setExpanded(expanded)}>
        <Container>
            <TagsInput ref={tagInputRef} onTagsChange={onFiltersChanged} />
        </Container>
    </StyledScrollableSection>;
});

export default TagsFilterSection;
