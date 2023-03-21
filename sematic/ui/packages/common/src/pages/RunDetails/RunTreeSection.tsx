import styled from '@emotion/styled';
import Typography from '@mui/material/Typography';

import theme from 'src/theme/new';
import RunTree from 'src/component/RunTree';

const Section = styled.section`
    display: flex;
    flex-direction: column;
    margin-bottom: ${theme.spacing(3)};
}
`
const Headline = styled.h2`
    margin-bottom: ${theme.spacing(3)};
`;

const StyledTypography = styled(Typography)`
    height: ${theme.spacing(10)};
    align-items: center;
    display: flex;
`;

const RunTreeSection = () => {
    const nodes = [
        {value: 'MNIST PyTorch Example', children: [
            {value: 'Load train dataset', children: [] as any},
            {value: 'Load test dataset', children: [] as any},
            {value: 'get_dataloader', children: [] as any},
            {value: 'get_dataloader', children: [] as any},
            {value: 'train_eval', children: [
                {value: 'train_model', children: [] as any},
                {value: 'evaluate_model', selected: true, children: [] as any}
            ] as any},
        ] as any}
       
    ]
    return <Section>
        <Headline>GRAPH</Headline>
        <StyledTypography >Execution Graph</StyledTypography>
        <RunTree runTreeNodes={nodes} />
    </Section>;
}

export default RunTreeSection;
