import styled from '@emotion/styled';
import theme from 'src/theme/new';

const Section = styled.section`
    padding-top: ${theme.spacing(2.4)};
`;

export const SectionWithBorder = styled(Section)`
    min-height: 50px;
    padding-top: 0;
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: center;

    &:after {
        content: '';
        position: absolute;
        bottom: 0;
        height: 1px;
        width: calc(100% + ${theme.spacing(10)});
        left: -${theme.spacing(5)};
        background: ${theme.palette.p3border.main};
    }
`;

export default Section;