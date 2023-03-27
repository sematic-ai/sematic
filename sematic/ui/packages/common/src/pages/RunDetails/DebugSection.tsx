import styled from '@emotion/styled';
import Link from '@mui/material/Link';
import theme from 'src/theme/new';
import Headline from 'src/component/Headline';
import Section from 'src/component/Section';

const StyledSection = styled(Section)`
    display: flex;
    flex-direction: column;
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
