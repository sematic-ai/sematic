import Typograph from '@mui/material/Typography';
import { useCallback } from 'react';
import TooltipManager from 'src/component/TooltipManager';

interface ImportPathProps {
    className?: string;
    style?: React.CSSProperties;
    children: React.ReactNode;
}

const ImportPath = (props: ImportPathProps) => {
    const { className, style, children } = props;

    const onRender = useCallback((ref: any) => (
        <Typograph ref={ref} variant='code' className={className} style={style || {}}>
            {children}
        </Typograph>
    ), [className, style, children]);

    return <TooltipManager text={children as string} onRender={onRender} />;
}

export default ImportPath;