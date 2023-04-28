import { useCallback } from 'react';
import ThreeColumns from "src/layout/ThreeColumns";
import CenterPane from 'src/pages/RunDetails/CenterPane';
import MetaDataPane from 'src/pages/RunDetails/MetaDataPane';
import NotesPane from 'src/pages/RunDetails/NotesPane';

const RunDetails = () => {

    const onRenderLeft = useCallback(() => {
        return <MetaDataPane />;
    }, []);

    const onRenderCenter = useCallback(() => {
        return <CenterPane />;
    }, []);

    const onRenderRight = useCallback(() => {
        return <NotesPane />;
    }, []);

    return <ThreeColumns onRenderLeft={onRenderLeft} onRenderCenter={onRenderCenter}
        onRenderRight={onRenderRight} />;
}

export default RunDetails;
