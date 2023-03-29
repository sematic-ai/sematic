import { MoreVert } from "@mui/icons-material";
import styled from "@emotion/styled";
import theme from "src/theme/new";

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

const MoreVertButton = (props: MoreVertButtonProps) => {
    const { className } = props;

    return <StyledButton className={className}><MoreVert /></StyledButton>;
}

export default MoreVertButton;