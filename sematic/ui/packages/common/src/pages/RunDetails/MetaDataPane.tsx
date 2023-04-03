import DebugSection from 'src/pages/RunDetails/DebugSection';
import GitSection from 'src/pages/RunDetails/GitSection';
import PipelineSection from 'src/pages/RunDetails/PipelineSection';
import RunSection from 'src/pages/RunDetails/RunSection';
import RunTreeSection from 'src/pages/RunDetails/RunTreeSection';

const MetaDataPane = () => {
    return <>
        <PipelineSection />
        <RunSection />
        <GitSection />
        <RunTreeSection />
        <DebugSection />
    </>;
}

export default MetaDataPane;
