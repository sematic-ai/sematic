import { css } from "@emotion/css";
import CloseIcon from "@mui/icons-material/Close";
import IconButton from "@mui/material/IconButton";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import { theme } from "@sematic/common/src/theme/mira";
import { useCallback } from "react";

const bannerStyle = css`
    background-color: rgb(229, 246, 253);
    padding: ${theme.spacing(2)};
    display: flex;
    align-items: center;
    justify-content: center;
    height: 30px;
    box-sizing: border-box;
    flex-grow: 0;
    flex-shrink: 0;

`;

const messageStyle = css`
    margin-right: ${theme.spacing(2)}!important;
    font-size: 16px!important;
`;

interface PromotionBannerProps {
    onClose: () => void;
}

const PromotionBanner = (props: PromotionBannerProps) => {
    const { onClose } = props;

    const switchToNewUI = useCallback(() => {
        window.localStorage.setItem("sematic-feature-flag-newui", "true");
        window.location.reload();
    }, []);

    return (
        <div className={bannerStyle}>
            <Typography variant="body1" className={messageStyle}>
                <Link style={{ cursor: "pointer" }} onClick={switchToNewUI}>
                    Try our new dashboard UI!
                </Link>
            </Typography>
            <IconButton size="small" aria-label="close" onClick={onClose} >
                <CloseIcon fontSize="small" />
            </IconButton>
        </div>
    );
};

export default PromotionBanner;