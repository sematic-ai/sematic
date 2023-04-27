import styled from '@emotion/styled';
import Box from '@mui/material/Box';
import { DateTimeLong, Duration } from 'src/component/DateTime';
import Headline from 'src/component/Headline';
import ImportPath from 'src/component/ImportPath';
import MoreVertButton from 'src/component/MoreVertButton';
import PipelineTitle from 'src/component/PipelineTitle';
import RunReferenceLink from "src/component/RunReferenceLink";
import { SuccessStateChip } from 'src/component/RunStateChips';
import Section from 'src/component/Section';
import TagsList from 'src/component/TagsList';
import theme from 'src/theme/new';

const StyledSection = styled(Section)`
    height: fit-content;
    min-height: 200px;
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
    
`;

const StyledVertButton = styled(MoreVertButton)`
    position: absolute;
    right: 0;
    top: 12px;
    transform: translate(50%,0);
`;

const BoxContainer = styled(Box)`
    display: flex;
    flex-direction: row;
    height: 35px;
    align-items: center;
    padding-top: ${theme.spacing(1)};
    margin-bottom: ${theme.spacing(4)};

    & .Info {
        margin-left: ${theme.spacing(2)};

        > div {
            display: flex;
            flex-direction: row;
            align-items: center;
            column-gap: ${theme.spacing(2)};
        }
    }
`;

const RunStateContainer = styled(Box)`
    flex-grow: 0;
    width: 25px;
`

const ImportPathContainer = styled(Box)`
    margin-bottom: ${theme.spacing(4)};
`

const StyledRunReferenceLink = styled(RunReferenceLink)`
    font-size: ${theme.typography.fontSize}px ;
`;

const FunctionName = PipelineTitle

const FunctionSection = () => {
    return <StyledSection>
        <Headline>Function Run</Headline>
        <BoxContainer>
            <RunStateContainer>
                <SuccessStateChip size={"large"} />
            </RunStateContainer>
            <div className='Info'>
                <FunctionName>
                    evaluate_model
                </FunctionName>
                <div>
                    <StyledRunReferenceLink runId={"qwc2ldf"} />
                    {`Completed in ${Duration("2012-04-23T18:14:23.511Z", "2012-04-23T18:25:43.511Z")} on ${DateTimeLong(new Date())}`}
                </div>
            </div>
        </BoxContainer>
        <ImportPathContainer>
            <ImportPath>examples.mnist.train_eval.evaluate_model</ImportPath>
        </ImportPathContainer>
        <StyledVertButton />
        <TagsList tags={['example', 'torch', 'mnist']} />
    </StyledSection>;
}

export default FunctionSection;
