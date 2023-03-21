import styled from '@emotion/styled';
import Typograph from '@mui/material/Typography';
import Box from '@mui/material/Box';
import MoreVertButton from 'src/component/MoreVertButton';

import theme from 'src/theme/new';

const HeadLine = styled.h2`
    margin: 0;
`;

const TopSection = styled.section`
    height: 100px;
    position: relative;
`;

const BottomSection = styled.section`
    height: 100px;
    border-bottom: 1px solid ${theme.palette.p3border.main};
    display: flex;
    margin: 0 -25px;
    & .MuiBox-root {
        width: 100px;
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

const PipelineSection = () => {
    return <>
        <TopSection>
            <HeadLine>PIPELINE</HeadLine>
            <Typograph variant='bold' style={{ marginTop: 15, marginBottom: 12 }}>MNIST PyTorch Example</Typograph>
            <Typograph variant='code'>examples.mnist.pipeline</Typograph>
            <StyledVertButton />
        </TopSection>
        <BottomSection>
            <Box>
                <Typograph variant='bigBold'>257</Typograph>
                <Typograph variant='body1'>runs</Typograph>
            </Box>
            <Box>
                <Typograph variant='bigBold'>74 min.</Typograph>
                <Typograph variant='body1'>avg. time</Typograph>
            </Box>
            <Box>
                <Typograph variant='bigBold'>62%</Typograph>
                <Typograph variant='body1'>success</Typograph>
            </Box>
        </BottomSection>
    </>;
}

export default PipelineSection;
