import styled from "@emotion/styled";
import Box from "@mui/material/Box";
import { buttonClasses } from "@mui/material/Button";
import Chip, { chipClasses } from "@mui/material/Chip";
import take from "lodash/take";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import useMeasure from "react-use/lib/useMeasure";
import theme, { SPACING } from "src/theme/new";

const MeasurementContainer = styled.div`
    position: absolute;
    visibility: hidden;
    width: max-content;

    & .${chipClasses.root}:not(*:last-of-type) {
        margin-right: ${theme.spacing(1)};
    }
`;

const StyledBox = styled(Box)`
    display: flex;
    align-items: center;
    flex-wrap: wrap;

    & .${chipClasses.root}:not(*:last-of-type) {
        margin-right: ${theme.spacing(1)};
    }

    & .${buttonClasses.root} {
        margin-left: ${theme.spacing(3)};
        padding: ${theme.spacing(1)};
        height: 25px;
    }

    & > .${chipClasses.root}, & > .${buttonClasses.root}{
        margin-bottom: ${theme.spacing(1)};
    }

    // This is to offset the margin-bottom set to the last row of elements
    margin-bottom: -${theme.spacing(1)}; 
`;

interface TagsListProps {
    tags: string[];
    fold?: number;
    onClick?: (tag: string) => void;
}

const TagsList = (props: TagsListProps) => {
    const { tags = [], onClick } = props;
    const [ref, { width }] = useMeasure();
    const [refMeasure, { width: measureWidth }] = useMeasure<HTMLDivElement>();
    const refMeasureDom = useRef<HTMLDivElement>();

    const setRef = useCallback((element: HTMLDivElement) => {
        refMeasureDom.current = element as HTMLDivElement;
        refMeasure(element);
    }, [refMeasure]);

    const [fold, setFold] = useState<number>(tags.length);

    const minFoldValue = useMemo(() => fold === 0 ? 1 : fold, [fold]);

    const plusMore = useMemo(() => {
        if (minFoldValue === tags.length) {
            return null;
        }
        return <Chip label={`+${tags.length - minFoldValue}`} variant={"tag"} />
    }, [tags, minFoldValue]);

    useEffect(() => {
        if (width < measureWidth) {
            const chips = refMeasureDom.current!.querySelectorAll('.tag-candiate');
            const widths = (Array.from(chips).map(chip => chip.getBoundingClientRect().width));
            let fold = 0, sum = 0; const gap = 40; // 40 is an estimation of the width of the "+{N}" chip

            while (fold < tags.length) {
                if (sum + widths[fold] + SPACING + gap > width) {
                    break;
                }
                sum += widths[fold] + SPACING;
                fold++;
            }
            setFold(fold);
        } else {
            setFold(tags.length);
        }

    }, [width, measureWidth, refMeasure, tags.length]);

    // Limit to 20 tags in trial rendering, to avoid too many tags in the UI
    // (Assume that the user will not need to see more than 20 tags in the actual display)
    const TagsInTrialRenderingLimit = useMemo(() => take(tags, 20), [tags]);

    return <div style={{ position: 'relative', width: '100%' }}>
        <MeasurementContainer ref={setRef}>
            {TagsInTrialRenderingLimit.map(tag => <Chip key={tag} className={"tag-candiate"} label={tag} variant={"tag"} />)}
        </MeasurementContainer>
        <StyledBox ref={ref}>
            {tags.map((tag, index) => {
                if (index >= minFoldValue) {
                    return null;
                }
                return <Chip key={tag} label={tag} variant={"tag"} onClick={() => onClick?.(tag)} />
            })}
            {plusMore}
        </StyledBox>
    </div>;
}

export default TagsList;