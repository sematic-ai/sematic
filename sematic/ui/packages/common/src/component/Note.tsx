import styled from "@emotion/styled";
import { KeyboardArrowDown } from "@mui/icons-material";
import Box from "@mui/material/Box";
import { useTheme } from "@mui/material/styles";
import Typography from "@mui/material/Typography";
import { useCallback, useMemo, useState } from "react";
import useMeasure from "react-use/lib/useMeasure";
import DateTime from "src/component/DateTime";
import NameTag from "src/component/NameTag";
import RunReferenceLink from "src/component/RunReferenceLink";
import Section from "src/component/Section";
import theme from "src/theme/new";

export interface Note {
    name: string;
    content: string;
    createdAt: string;
    runId: string;
}

type ExtendedStyleProps = {
    isExpanded?: boolean;
    contentHeight?: number;
}

const footerHeight = 20;

const Container = styled(Section, {
    shouldForwardProp: (prop) => !["isExpanded", "contentHeight"].includes(prop as any),
}) <ExtendedStyleProps>`
    min-height: 100px;
    height: ${props => props.isExpanded ? 'max-content' : '100px'};
    padding-bottom: calc(${footerHeight}px);
    box-sizing: border-box;
    position: relative;
    overflow: ${props => props.isExpanded ? "visible" : "hidden"};

    &:after {
        content: '';
        height: 1px;
        background: ${theme.palette.p3border.main};
        width: calc(100% + ${theme.spacing(4.8)});
        position: absolute;
        bottom: 0;
        margin-left: -${theme.spacing(2.4)};
    }
`;

const Title = styled(Box)`
    height: 15px;
    line-height: 15px;
    margin-bottom: ${theme.spacing(2)};
    display: flex;
    justify-content: space-between;
`;

const StyledRunReferenceLink = styled(RunReferenceLink)`
    margin-left: ${theme.spacing(1)};
`;

const Body = styled(Box)`
    font-size: ${theme.typography.small.fontSize}px;
`;

const Footer = styled(Box,  {
    shouldForwardProp: (prop) => !["isExpanded", "contentHeight"].includes(prop as any),
}) <ExtendedStyleProps>`
    height: ${footerHeight}px;
    box-sizing: content-box;
    display: flex;
    flex-direction: row;
    justify-content: flex-end;
    position: absolute;
    width: 100%;
    padding-bottom: ${theme.spacing(1)};
    bottom: 0;
    background-image: linear-gradient(rgba(255,255,255,0), ${theme.palette.background.paper} 60%);

    & svg {
        cursor: pointer;
        transform: ${props => props.isExpanded ? "rotate(180deg)" : "rotate(0deg)"};
        transition: transform 200ms cubic-bezier(0.4, 0, 0.2, 1) 0ms;
    }
`;

interface NoteProps extends Note {
}

const NoteComponent = (prop: NoteProps) => {
    const { name, content, createdAt, runId } = prop;

    const theme = useTheme();
    const [isExpanded, setIsExpanded] = useState(false);

    const [containerRef, { height: containerHeight }] = useMeasure<HTMLDivElement>();
    const [contentArea, { height: contentHeight }] = useMeasure<HTMLDivElement>();

    const shouldShowControl = useMemo(() => contentHeight > containerHeight, [containerHeight, contentHeight]);

    const onControlClick = useCallback(() => {
        setIsExpanded(!isExpanded);
    }, [isExpanded, setIsExpanded]);

    return <Container ref={containerRef} isExpanded={isExpanded} contentHeight={contentHeight} >
        <div ref={contentArea}>
            <Title>
                <Box style={{ display: 'flex' }}>
                    <NameTag>{name}</NameTag>
                    <Typography variant="small" color={theme.palette.lightGrey.main} paragraph={false}>
                        {"\xa0on run"}
                    </Typography>
                    <StyledRunReferenceLink runId={runId} />
                </Box>
                <DateTime datetime={createdAt} />
            </Title>
            <Body>
                {content}
            </Body>
        </div>
        <Footer isExpanded={isExpanded}>
            {(shouldShowControl || isExpanded) && <KeyboardArrowDown onClick={onControlClick} />}
        </Footer>
    </Container>
};

export default NoteComponent;
