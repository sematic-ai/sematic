import styled from '@emotion/styled';
import Link from '@mui/material/Link';

import theme from 'src/theme/new';

const Section = styled.section`
    display: flex;
    flex-direction: column;
}
`
const Headline = styled.h2`
    margin-bottom: ${theme.spacing(3)};
`;

const StyledLink = styled(Link)`
    margin-top: ${theme.spacing(3)};
    margin-bottom: ${theme.spacing(3)};
`;

const DebugSection = () => {
    return <Section>
        <Headline>DEBUG</Headline>
        <StyledLink >Resolution logs</StyledLink>
        <StyledLink >Build information</StyledLink>
    </Section>;
}

export default DebugSection;
