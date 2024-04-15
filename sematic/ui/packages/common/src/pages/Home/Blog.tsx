import styled from "@emotion/styled";
import Link from "@mui/material/Link";
import Typography, { typographyClasses } from "@mui/material/Typography";
import blogData from "@sematic/common/src/pages/Home/blogs.json";
import theme from "src/theme/new";

const Container = styled.div`
    height: 100%;
    overflow-y: auto;
    scroller-gutter: stable;
    margin-left: -${theme.spacing(5)};
    margin-right: -${theme.spacing(5)};
`;

const StyledSection = styled.section`
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
    height: 50px;
    margin-top: -${theme.spacing(2)};
    padding-left: ${theme.spacing(5)};
    padding-right: ${theme.spacing(5)};

    font-size: ${theme.typography.fontSize}px;
    font-weight: ${theme.typography.fontWeightBold};

    a {
        margin-right: 0;
    }
`;


const BlogWrapper = styled.div`
    min-height: 100px;
    margin: 0;
    padding: ${theme.spacing(2)} ${theme.spacing(5)};
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: flex-start;
    font-size: ${theme.typography.fontSize}px;

    & .${typographyClasses.root} {
        font-size: ${theme.typography.fontSize}px;
    }

    & a {
        font-weight: ${theme.typography.fontWeightBold};
        color: ${theme.palette.primary.main};
    }

    & svg {
        cursor: pointer;
    }
`;

const StyledTypography = styled(Typography)`
    margin: ${theme.spacing(1)} 0;
`;

export default function Blog() {
    return <Container>
        <StyledSection>
            <span>
                Latest blog posts
            </span>
            <span>
                <Link variant="subtitle1" type="menu" target={"_blank"} href={"https://www.sematic.dev/blog"}>
                    See all
                </Link>
            </span>
        </StyledSection>
        {blogData.map(({title, link, description, author, time}: any, i) => <BlogWrapper key={i}>
            <Link target={"_blank"} href={link}>{title}</Link>
            <StyledTypography>{description}</StyledTypography>
            <Typography color={"lightGray"}>{`${author} on ${time}.`}</Typography>
        </BlogWrapper>)}
    </Container>;
}
