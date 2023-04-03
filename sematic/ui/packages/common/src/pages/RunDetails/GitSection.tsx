import styled from '@emotion/styled';

import theme from 'src/theme/new';
import GitInfoBox from 'src/component/GitInfo';
import Section from 'src/component/Section';
import Headline from 'src/component/Headline';

const StyledSection = styled(Section)`
    display: flex;
    flex-direction: column;
    margin-bottom: ${theme.spacing(4)};
}
`
const GitSection = () => {
    return <StyledSection>
        <Headline>Git</Headline>
        <GitInfoBox hasUncommittedChanges={true}/>
    </StyledSection>;
}

export default GitSection;
