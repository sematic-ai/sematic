import styled from '@emotion/styled';
import Box from '@mui/material/Box';
import Typograph from '@mui/material/Typography';
import Headline from 'src/component/Headline';
import ImportPath from 'src/component/ImportPath';
import MoreVertButton from 'src/component/MoreVertButton';
import PipelineTitle from 'src/component/PipelineTitle';
import Section from 'src/component/Section';
import theme from 'src/theme/new';

const TopSection = styled(Section)`
    height: 100px;
    min-height: 100px;
    position: relative;
`;

const BottomSection = styled.section`
    height: 100px;
    border-bottom: 1px solid ${theme.palette.p3border.main};
    display: flex;
    margin: 0 -25px;
    & .MuiBox-root {
        width: 100px;
        min-height: 100px;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
`;

const StyledVertButton = styled(MoreVertButton)`
    position: absolute;
    right: 0;
    top: 12px;
    transform: translate(50%,0);
`;

const StyledPipelineTitle = styled(PipelineTitle)`
    margin-bottom: ${theme.spacing(2.4)};
    margin-right: ${theme.spacing(2)};
`

const PipelineSection = () => {
    return <>
        <TopSection>
            <Headline>Pipeline</Headline>
            <StyledPipelineTitle>
                MNIST PyTorch Example
            </StyledPipelineTitle>
            <ImportPath>sematic.examples.mnist.pipeline.with.very.long.path</ImportPath>
            <StyledVertButton />
        </TopSection>
        <BottomSection>
            <Box>
                <Typograph variant='bigBold'>257</Typograph>
                <Typograph variant='body1'>runs</Typograph>
            </Box>
            <Box>
                <Typograph variant='bigBold'>74 min.</Typograph>
                <Typograph variant='body1'>average time</Typograph>
            </Box>
            <Box>
                <Typograph variant='bigBold'>62%</Typograph>
                <Typograph variant='body1'>success rate</Typograph>
            </Box>
        </BottomSection>
    </>;
}

export default PipelineSection;
