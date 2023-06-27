import Typograph from "@mui/material/Typography";
import { forwardRef } from "react";
import PipelineTitle from "src/component/PipelineTitle";

interface NameTagProps {
    firstName?: string | null;
    lastName?: string | null;
    variant?: React.ComponentProps<typeof Typograph>["variant"];
    className?: string;
}

const NameTag = forwardRef<HTMLElement, NameTagProps>((props, ref) => {
    const { firstName, lastName, className, variant = "small" } = props;

    const name = !!firstName && !!lastName ? `${firstName} ${lastName}` : firstName || lastName || "Unknown";

    return <span style={{ maxWidth: "100px" }} ref={ref} className={className}>
        <PipelineTitle variant={variant} >
            {name}
        </PipelineTitle>
    </span>;
});

export default NameTag;
