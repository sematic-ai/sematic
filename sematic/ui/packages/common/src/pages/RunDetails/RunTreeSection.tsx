import styled from '@emotion/styled';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';
import theme from 'src/theme/new';
import RunTree from 'src/component/RunTree';
import Section from 'src/component/Section';
import Headline from 'src/component/Headline';

const StyledSection = styled(Section)`
    display: flex;
    flex-direction: column;
`

const ScrollableStyledSection = styled(StyledSection)`
    margin-top: 0;
    margin-bottom: ${theme.spacing(3)};
    overflow-y: auto;
    overflow-x: hidden;
    direction: rtl;
    margin-left: -25px;
    margin-right: -25px;
    scrollbar-gutter: stable;
    flex-shrink: 1!important;

    &::-webkit-scrollbar {
      display: block;
      width: 16px;
    }
    
    &::-webkit-scrollbar-button {
      display: none;
    }
    
    &::-webkit-scrollbar-track {
      background-color: #00000000;
    }
    
    &::-webkit-scrollbar-track-piece {
      background-color: #00000000;
    }
    
    &::-webkit-scrollbar-thumb {
      background-color: #00000040;
      border: 1px solid #ffffff40;
      border-radius: 24px;
    }

    &::-webkit-scrollbar-thumb:hover {
        background-color: #00000060;
    }

`;

const StyledTypography = styled(Typography)`
    height: ${theme.spacing(6)};
    align-items: center;
    display: flex;
`;
const RunTreeContainer = styled(Box)`
    direction: ltr;
    margin-left: ${theme.spacing(2)};
`;

const RunTreeSection = () => {
    const nodes = [
        {
            value: 'MNIST PyTorch Example', children: [
                { value: 'Load train dataset', children: [] as any },
                { value: 'Load test dataset', children: [] as any },
                { value: 'get_dataloader', children: [] as any },
                { value: 'get_dataloader', children: [] as any },
                {
                    value: 'train_eval', children: [
                        { value: 'train_model', children: [] as any },
                        { value: 'evaluate_model', selected: true, children: [] as any }
                    ] as any
                },
            ] as any
        }

    ]

    return <>
        <StyledSection>
            <Headline>Graph</Headline>
            <StyledTypography >Execution Graph</StyledTypography>
        </StyledSection>
        <ScrollableStyledSection>
            <RunTreeContainer>
                <RunTree runTreeNodes={nodes} />
            </RunTreeContainer>
        </ScrollableStyledSection>
    </>;
}

export default RunTreeSection;
