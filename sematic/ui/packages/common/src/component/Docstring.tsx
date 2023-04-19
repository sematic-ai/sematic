import { KeyboardArrowDown } from "@mui/icons-material";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import { useTheme } from "@mui/material/styles";
import ReactMarkdown from "react-markdown";
import useMeasure from "react-use/lib/useMeasure";
import { useMemo, useState, useCallback } from "react";
import styled from "@emotion/styled";
import theme from "src/theme/new";

const Container = styled(Box, {
    shouldForwardProp: (prop) => !["shouldShowControl", "isExpanded"].includes(prop as any),
}) <{
    isExpanded?: boolean;
    shouldShowControl?: boolean;
}>`
    display: flex;
    position: relative;
    min-height: 50px;
    height: ${props => props.isExpanded ? 'max-content' : '40px'};
    overflow: ${props => props.isExpanded ? "visible" : "hidden"};

    & > .MarkdownWrapper {
        height: max-content;

        p {
            font-size: ${theme.typography.fontSize}px;
        }
    }

    &:after {
        ${props => (props.isExpanded || !props.shouldShowControl) ? 'display: none' : ''};
        content: '';
        height: 25px;
        background-image: linear-gradient(rgba(255,255,255,0), ${theme.palette.background.paper} 60%);
        position: absolute;
        pointer-events: none;
        bottom: 0;
        width: 100%;
        z-index: 1;
    }
`;

const Footer = styled(Box, {
    shouldForwardProp: (prop) => prop !== "isExpanded",
}) <{
    isExpanded?: boolean;
}>`
    position: absolute;
    right: 0;
    bottom: 0;
    height: min-content;
    line-height: 1;
    z-index: 2;

    & svg {
        cursor: pointer;
        transform: ${props => props.isExpanded ? "rotate(180deg)" : "rotate(0deg)"};
        transition: transform 200ms cubic-bezier(0.4, 0, 0.2, 1) 0ms;
    }
`;

export interface DocstringProps {
    docstring: string | undefined | null;
}

const Docstring = (props: DocstringProps) => {
    const { docstring } = props;
    const theme = useTheme();
    const [isExpanded, setIsExpanded] = useState(false);


    const [containerRef, { height: containerHeight }] = useMeasure<HTMLDivElement>();
    const [contentArea, { height: contentHeight }] = useMeasure<HTMLDivElement>();

    const shouldShowControl = useMemo(() => contentHeight > containerHeight, [containerHeight, contentHeight]);

    const onControlClick = useCallback(() => {
        setIsExpanded(!isExpanded);
    }, [isExpanded, setIsExpanded]);

    return <Container ref={containerRef} isExpanded={isExpanded} shouldShowControl={shouldShowControl}>
        {(docstring !== undefined && docstring !== null && (
            <Box ref={contentArea} className={"MarkdownWrapper"}>
                <ReactMarkdown>{docstring}</ReactMarkdown>
            </Box>
        )) || (
                <Typography color={theme.palette.lightGrey.main}>
                    Your function's docstring will appear here.
                </Typography>
            )}
        {(shouldShowControl || isExpanded) && <Footer isExpanded={isExpanded} >
            <KeyboardArrowDown onClick={onControlClick} />
        </Footer>}
    </Container>
}

export default Docstring
