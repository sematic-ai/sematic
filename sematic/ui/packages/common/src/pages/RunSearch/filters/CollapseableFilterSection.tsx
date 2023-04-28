import styled from '@emotion/styled';
import { KeyboardArrowDown } from "@mui/icons-material";
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import { SectionWithBorder } from 'src/component/Section';
import theme from 'src/theme/new';

const BoldHeader = styled.div`
    font-weight: ${theme.typography.fontWeightBold};
`;

const StyledAccordion = styled(Accordion)`
    max-height: 100%;
`;

interface CollapseableFilterSectionProps {
    title: string;
    children: React.ReactNode;
    className?: string;
}

const CollapseableFilterSection = (props: CollapseableFilterSectionProps) => {
    const { title, children, className } = props;
    return <SectionWithBorder className={className}>
        <StyledAccordion>
            <AccordionSummary expandIcon={<KeyboardArrowDown />} >
                <BoldHeader>{title}</BoldHeader>
            </AccordionSummary>
            <AccordionDetails>
                {children}
            </AccordionDetails>
        </StyledAccordion>
    </SectionWithBorder>;
}

export default CollapseableFilterSection;
