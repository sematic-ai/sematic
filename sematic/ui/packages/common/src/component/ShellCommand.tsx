import styled from "@emotion/styled";
import { ContentCopy } from "@mui/icons-material";
import { useTheme } from "@mui/material";
import ButtonBase from "@mui/material/ButtonBase";
import { CSSProperties, useCallback, useState } from "react";
import theme from "src/theme/new";

interface ShellCommandProps {
    command: string;
    className?: string;
    style?: CSSProperties;
}

function ShellCommand(props: ShellCommandProps) {
    const { command, className, style } = props;

    const [content, setContent] = useState("$ " + command);

    const theme = useTheme();

    const onClick = useCallback(() => {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(command);
        }
        setContent("Copied!");
        setTimeout(() => setContent("$ " + command), 1000);
    }, [command]);

    return (
        <ButtonBase
            sx={{
                backgroundColor: theme.palette.grey[800],
                color: theme.palette.grey[100],
                py: 1,
                px: 2,
                borderRadius: 1,
                display: "flex",
                width: "100%",
                textAlign: "left",
                boxShadow: "rgba(0,0,0,0.5) 0px 0px 5px 0px",
            }}
            onClick={onClick}
            className={className}
            style={style}
        >
            <code style={{ flexGrow: 1 }}>{content}</code>
            <ContentCopy fontSize="small" sx={{ color: theme.palette.grey[600] }} />
        </ButtonBase>
    );
}

export const ShellCommandRelaxed = styled(ShellCommand)`
    padding-top: ${theme.spacing(5)};
    padding-bottom: ${theme.spacing(5)};

    background-color: ${theme.palette.black.main};
`;

export default ShellCommand;
