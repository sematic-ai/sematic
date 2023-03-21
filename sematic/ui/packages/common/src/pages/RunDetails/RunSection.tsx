import styled from '@emotion/styled';
import Box from '@mui/material/Box';
import { useTheme } from '@mui/material/styles';
import Typography, { typographyClasses } from '@mui/material/Typography';
import MoreVertButton from 'src/component/MoreVertButton';
import RunsDropdown from 'src/component/RunsDropdown';
import theme from 'src/theme/new';
import TagsList from 'src/component/TagsList';

const Section = styled.section`
    margin-bottom: ${theme.spacing(3)};
`;

const StyledVertButton = styled(MoreVertButton)`
    transform: translate(50%,0);
`;

const BoxContainer = styled(Box)`
    display: flex;
    & .${typographyClasses.root} {
        margin-right: ${theme.spacing(2)};
    }
`
const RunSection = () => {
    const theme = useTheme();

    return <Section>
            <h2>RUN</h2>
            <BoxContainer style={{marginBottom: theme.spacing(3)}}>
                <RunsDropdown />
                <StyledVertButton />
            </BoxContainer>
            <BoxContainer style={{marginBottom: theme.spacing(2)}}>
                <Typography variant='small'>Developer E.</Typography>
                <Typography variant='small'>CloudResolver</Typography>
            </BoxContainer>
            <BoxContainer>
                <TagsList tags={['example', 'torch', 'mnist']} />
            </BoxContainer>
        </Section>
    ;
}

export default RunSection;
