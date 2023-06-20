import { MoreVert } from "@mui/icons-material";
import styled from "@emotion/styled";
import theme from "src/theme/new";
import { forwardRef } from "react";

interface MoreVertButtonProps {
    className?: string;
}

const StyledButton = styled.button`
    width: 25px;
    height: 25px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    background: transparent;
    cursor: pointer;

    &:hover {
        color: ${theme.palette.primary.main}
    }
`;

const MoreVertButton = forwardRef<HTMLButtonElement | null, MoreVertButtonProps>(
    (props: MoreVertButtonProps, ref) => {
        const { className } = props;

        return <StyledButton ref={ref} className={className}><MoreVert /></StyledButton>;
    });

export default MoreVertButton;