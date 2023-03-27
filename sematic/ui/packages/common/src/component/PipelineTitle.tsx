import Typograph from '@mui/material/Typography';
import { useCallback } from 'react';
import TooltipManager from 'src/component/TooltipManager';

interface PipelineTitleProps {
    className?: string;
    style?: React.CSSProperties;
    children: React.ReactNode;
}

const PipelineTitle = (props: PipelineTitleProps) => {
    const { className, style, children } = props;

    const onRender = useCallback((ref: any) => (
        <Typograph ref={ref} variant='bold' className={className} style={style || {}}>
            {children}
        </Typograph>
    ), [className, style, children]);

    return <TooltipManager text={children as string} onRender={onRender} />;
}

export default PipelineTitle;