import Tooltip from '@mui/material/Tooltip';
import React from 'react';
import { useMemo } from 'react';
import useMeasure, { UseMeasureRef } from "react-use/lib/useMeasure";

interface TooltipManagerProps {
    text: string;
    onRender: (ref: UseMeasureRef<Element>) => React.ReactElement;
}

/**
 * This component is used to manage the tooltip of a component. 
 * It will render the component twice, once for the presentation and once for the measurement.
 * The measurement component will be hidden and will not take up space,
 * and will be used to measure the width of the presentation component if fully expanded. 
 * The presentation component will be used to render the actual component.
 * If the width of the presentation component is less than the measurement component, then the tooltip will be shown. 
 * 
 * @param props 
 * @returns 
 */
const TooltipManager = (props: TooltipManagerProps) => {
    const { onRender, text } = props;

    const [refPresentation, { width: widthPresentation }] = useMeasure();

    const presentation = useMemo(() => {
        const element = onRender(refPresentation);
        // The real presentatin will use ellipsis if applicable.
        element.props.style.textOverflow = 'ellipsis';
        element.props.style.overflow = 'hidden';
        element.props.style.whiteSpace = 'nowrap';
        return element;
    }, [onRender, refPresentation]);

    const [refMeasure, { width: widthMeasure }] = useMeasure();

    const measurement = useMemo(() => {
        const element = onRender(refMeasure);
        element.props.style.position = 'absolute'; // set this so it does not take up space
        element.props.style.visibility = 'hidden';
        element.props.style.width = 'max-content';
        return element;
    }, [onRender, refMeasure]);

    const shouldShowTooltip = widthPresentation < widthMeasure;

    return <>
        {measurement}
        <Tooltip title={text} arrow={true} disableHoverListener={!shouldShowTooltip}>
            {presentation}
        </Tooltip>
    </>;
}

export default TooltipManager;