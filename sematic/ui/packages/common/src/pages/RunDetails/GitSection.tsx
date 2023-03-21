import styled from '@emotion/styled';

import theme from 'src/theme/new';
import GitInfoBox from 'src/component/GitInfo';

const Headline = styled.h2`
    margin-bottom: ${theme.spacing(3)};
`;
const Section = styled.section`
    display: flex;
    flex-direction: column;
    margin-bottom: ${theme.spacing(4)};
}
`
const GitSection = () => {
    return <Section>
        <Headline>GIT</Headline>
        <GitInfoBox />
    </Section>;
}

export default GitSection;
