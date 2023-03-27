import { useCallback } from 'react';
import ThreeColumns from "src/layout/ThreeColumns";
import MetaDataPane from 'src/pages/RunDetails/MetaDataPane';

const RunDetails = () => {

    const onRenderLeft = useCallback(() => {
        return <MetaDataPane />;
    }, []);

    return <ThreeColumns onRenderLeft={onRenderLeft} />;
}

export default RunDetails;
