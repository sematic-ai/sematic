import React, { useState, useCallback } from "react";
import Accordion from "@mui/material/Accordion";
import AccordionSummary from "@mui/material/AccordionSummary";
import AccordionDetails from "@mui/material/AccordionDetails";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import Typography from "@mui/material/Typography";
import { CommonValueViewProps } from "./common";

const SUMMARY_MAX_LENGTH = 100;

export default function PromptResponseValueView(props: CommonValueViewProps) {
    let { valueSummary } = props;
    let { values } = valueSummary;
    const prompt = values.prompt;
    const response = values.response;

    const promptComponent = (<TextSummaryAccordion text={prompt} textKind={"Prompt"} />);
    const responseComponent = (<TextSummaryAccordion text={response} textKind={"Response"} />);

    return (
        <div>
            {promptComponent}
            {responseComponent}
        </div>
    );
}

interface TextSummaryAccordionProps {
    text: string;
    textKind: string;
}

function TextSummaryAccordion(props: TextSummaryAccordionProps) {
    let { text, textKind } = props;
    const [expanded, setExpanded] = useState<boolean>(false);

    const handleChange = useCallback(() => {
        setExpanded(!expanded);
    }, [expanded]);

    const textIsLong = text.length > SUMMARY_MAX_LENGTH; 
    const shortText = (
        textIsLong ?
            text.substring(0, SUMMARY_MAX_LENGTH) + "..." :
            text
    );
    const textJsx = text.split("\n").map((str: string) => <p>{str}</p>);
    const textColor = textIsLong ? "text.secondary" : "text.primary";
    const expandIcon = textIsLong ? (<ExpandMoreIcon />) : (<div/>);
    const cursor = textIsLong ? "pointer" : "default";

    return (
        <Accordion
            expanded={expanded && textIsLong}
            onChange={handleChange}
            style={{cursor: cursor}}
        >
            <AccordionSummary
                expandIcon={expandIcon}
                style={{cursor: cursor}}
            >
                <Typography sx={{ width: "15%", flexShrink: 0, fontWeight: "bolder" }}>
                    {textKind}
                </Typography>
                <Typography sx={{ color: textColor }}>{shortText}</Typography>
            </AccordionSummary>
            <AccordionDetails>
                <Typography >{textJsx}</Typography>
            </AccordionDetails>
        </Accordion>
    );
}
