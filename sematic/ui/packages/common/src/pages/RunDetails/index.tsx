import { useCallback } from 'react';
import ThreeColumns from "src/layout/ThreeColumns";
import MetaDataPane from 'src/pages/RunDetails/MetaDataPane';
import NotesPane from 'src/pages/RunDetails/NotesPane';

const RunDetails = () => {

    const onRenderLeft = useCallback(() => {
        return <MetaDataPane />;
    }, []);

    const onRenderRight = useCallback(() => {
        return <NotesPane />;
    }, []);

    return <ThreeColumns onRenderLeft={onRenderLeft} onRenderRight={onRenderRight} />;
}

export default RunDetails;
