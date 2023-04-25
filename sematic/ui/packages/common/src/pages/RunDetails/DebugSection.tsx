import styled from '@emotion/styled';
import Link from '@mui/material/Link';
import theme from 'src/theme/new';
import Headline from 'src/component/Headline';
import Section from 'src/component/Section';

const StyledSection = styled(Section)`
    display: flex;
    flex-direction: column;
    position: relative;

    &:after {
        content: '';
        position: absolute;
        bottom: 0;
        height: 1px;
        width: calc(100% + ${theme.spacing(10)});
        margin-left: -${theme.spacing(5)};
        background: ${theme.palette.p3border.main};
    }
}
`
const StyledLink = styled(Link)`
    margin-top: ${theme.spacing(2)};
    margin-bottom: ${theme.spacing(2)};
`;

const DebugSection = () => {
    return <StyledSection>
        <Headline>Debug</Headline>
        <StyledLink >Resolution logs</StyledLink>
        <StyledLink >Build information</StyledLink>
    </StyledSection>;
}

export default DebugSection;
