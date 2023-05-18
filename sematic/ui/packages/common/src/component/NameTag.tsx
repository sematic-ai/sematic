import React from "react";
import PipelineTitle from "src/component/PipelineTitle";

interface NameTagProps {
    firstName?: string | null;
    lastName?: string | null;
}

const NameTag = (props: NameTagProps ) => {
    const { firstName, lastName } = props;

    const name = !!firstName && !!lastName ? `${firstName} ${lastName}` : firstName || lastName || "Unknown";

    return <span style={{ maxWidth: "100px" }}>
        <PipelineTitle variant={"small"} >
            {name}
        </PipelineTitle>
    </span>;
}

export default NameTag;
