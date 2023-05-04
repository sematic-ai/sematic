import styled from '@emotion/styled';
import { KeyboardArrowDown } from "@mui/icons-material";
import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import { collapseClasses } from '@mui/material/Collapse';
import { paperClasses } from '@mui/material/Paper';
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
    onChange?: (event: React.SyntheticEvent, expanded: boolean) => void;
}

const CollapseableFilterSection = (props: CollapseableFilterSectionProps) => {
    const { title, children, className, onChange } = props;
    return <SectionWithBorder className={className}>
        <StyledAccordion onChange={onChange}>
            <AccordionSummary expandIcon={<KeyboardArrowDown />} >
                <BoldHeader>{title}</BoldHeader>
            </AccordionSummary>
            <AccordionDetails style={{minHeight: 50}}>
                {children}
            </AccordionDetails>
        </StyledAccordion>
    </SectionWithBorder>;
}

export const ScrollableCollapseableFilterSection = styled(CollapseableFilterSection)`
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

export default CollapseableFilterSection;
