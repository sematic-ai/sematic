import styled from "@emotion/styled";
import ChevronRight from "@mui/icons-material/ChevronRight";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import { ReactNode, useCallback, useRef } from "react";
import Headline from "src/component/Headline";
import { CommunityLinks } from "src/pages/GettingStarted";
import theme from "src/theme/new";

const Container = styled.div`
    height: 100%;
    overflow-y: auto;
    scroller-gutter: stable;
    margin-left: -${theme.spacing(5)};
    margin-right: -${theme.spacing(5)};
`;

const StyledHeadline = styled(Headline)`
    margin-left: ${theme.spacing(5)};
    margin-top: -${theme.spacing(2)};
    margin-bottom: 0;
    height: 50px;
    display: flex;
    align-items: center;
    color: ${theme.palette.black.main};
`;

const LinkWrapper = styled.div`
    margin: 0;
    padding: 0 0 0 ${theme.spacing(5)};
    position: relative;
    display: flex;
    justify-content: space-between;
    align-items: center;

    &:after {
        content: "";
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 1px;
        background-color: ${theme.palette.p3border.main};
    }

    & a {
        color: ${theme.palette.black.main};

        &:hover {
            color: ${theme.palette.primary.main};
        }
    }

    & svg {
        cursor: pointer;
    }
`;

const StyledTypography = styled(Typography)`
    margin: ${theme.spacing(5)};    
`;

function LinkEntry({ link }: {link: ReactNode}) {
    const ref = useRef<HTMLDivElement>(null);

    const onClick = useCallback(() => {
        ref.current?.querySelector("a")?.click();
    }, []);

    return <LinkWrapper ref={ref}>
        {link}
        <ChevronRight onClick={onClick} />
    </LinkWrapper>
}

function onRenderLinkEntry(link: ReactNode) {
    return <LinkEntry link={link} />
}

export default function Community() {
    return <Container>
        <StyledHeadline>Community</StyledHeadline>
        <CommunityLinks onRenderLinkEntry={onRenderLinkEntry} />
        <StyledTypography>If you have any questions, email us at&nbsp; 
            <Link href="mailto:support@sematic.dev">support@sematic.dev.</Link></StyledTypography>
    </Container>;
}