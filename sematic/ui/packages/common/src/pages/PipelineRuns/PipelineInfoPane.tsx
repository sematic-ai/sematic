import Headline from "src/component/Headline";
import Section from "src/component/Section";
import PipelineSection from "src/pages/RunDetails/PipelineSection";
import SearchFilters from "src/pages/RunSearch/SearchFilters";
import { AllFilters } from "src/pages/RunTableCommon/filters";
import styled from "@emotion/styled";
import theme from "src/theme/new";

const TopSection = styled(Section)`
  height: 50px;
  position: relative;
  display: flex;
  align-items: center;

  &::after {
    content: "";
    position: absolute;
    left: -${theme.spacing(5)};
    bottom: 0;
    right: -${theme.spacing(5)};
    height: 1px;
    background-color: ${theme.palette.p3border.main};
 }
`;

interface PipelineInfoPaneProps {
    onFiltersChanged: (filters: AllFilters) => void;
}

function PipelineInfoPane(props: PipelineInfoPaneProps) {
    const { onFiltersChanged } = props;

    return <>
        <PipelineSection />
        <TopSection>
            <Headline>Filters</Headline>
        </TopSection>
        <SearchFilters onFiltersChanged={onFiltersChanged} />
    </>;
}

export default PipelineInfoPane;