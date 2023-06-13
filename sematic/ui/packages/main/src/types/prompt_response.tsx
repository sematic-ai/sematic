import React, { SyntheticEvent, useState } from "react";
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
    const [expanded, setExpanded] = useState<string | false>(false);

    const handleChange = (panel: string) => (event: SyntheticEvent, isExpanded: boolean) => {
        setExpanded(isExpanded ? panel : false);
    };
    let shortPrompt = (
        values.prompt.length > SUMMARY_MAX_LENGTH ?
            values.prompt.substring(0, SUMMARY_MAX_LENGTH) + "..." :
            values.prompt
    );
    const promptJsx = values.prompt.split("\n").map((str: string) => <p>{str}</p>);
    let shortResponse = (
        values.response.length > SUMMARY_MAX_LENGTH ?
            values.response.substring(0, SUMMARY_MAX_LENGTH) + "..." :
            values.response
    );
    const responseJsx = values.response.split("\n").map((str: string) => <p>{str}</p>);

    return (
        <div>
            <Accordion expanded={expanded === "panel1"} onChange={handleChange("panel1")}>
                <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    aria-controls="panel1bh-content"
                    id="panel1bh-header"
                >
                    <Typography sx={{ width: "33%", flexShrink: 0, fontWeight: "bolder" }}>
                      Prompt
                    </Typography>
                    <Typography sx={{ color: "text.secondary" }}>{shortPrompt}</Typography>
                </AccordionSummary>
                <AccordionDetails>
                    <Typography >{promptJsx}</Typography>
                </AccordionDetails>
            </Accordion>
            <Accordion expanded={expanded === "panel2"} onChange={handleChange("panel2")}>
                <AccordionSummary
                    expandIcon={<ExpandMoreIcon />}
                    aria-controls="panel2bh-content"
                    id="panel2bh-header"
                >
                    <Typography sx={{ width: "33%", flexShrink: 0, fontWeight: "bolder" }}>
                      Response
                    </Typography>
                    <Typography sx={{ color: "text.secondary" }}>{shortResponse}</Typography>
                </AccordionSummary>
                <AccordionDetails>
                    <Typography >{responseJsx}</Typography>
                </AccordionDetails>
            </Accordion>
        </div>
    );
}
