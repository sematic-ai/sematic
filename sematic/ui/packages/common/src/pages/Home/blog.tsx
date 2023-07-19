import styled from "@emotion/styled";
import Link from "@mui/material/Link";
import Typography, { typographyClasses } from "@mui/material/Typography";
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
    height: 100px;
    margin: 0;
    padding: ${theme.spacing(2)} ${theme.spacing(5)};
    position: relative;
    border-bottom: 1px solid ${theme.palette.p3border.main};
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: flex-start;
    font-size: ${theme.typography.fontSize}px;

    & .${typographyClasses.root} {
        font-size: ${theme.typography.fontSize}px;
    }

    & a {
        color: ${theme.palette.primary.main};
    }

    & svg {
        cursor: pointer;
    }
`;

const TypographyDescription = styled(Typography)`
    -webkit-line-clamp: 2;
    overflow: hidden;
    display: -webkit-box;
    -webkit-box-orient: vertical;
`;

export default function Blog() {
    return <Container>
        <StyledSection>
            <span>
                Latest blog pipelines
            </span>
            <span>
                <Link variant="subtitle1" type='menu' target={"_blank"} href={"https://www.sematic.dev/blog"}>
                    See all
                </Link>
            </span>
        </StyledSection>
        <BlogWrapper >
            <Link target={"_blank"} href="https://www.sematic.dev/blog/tuning-and-serving-flan-t5-and-gpt-j-6b-with-lora-sematic-and-gradio">
            Tuning and serving FLAN-T5 and GPT-J 6B with LoRA, Sematic, and Gradio
            </Link>
            <TypographyDescription>
            Fine-tune FLAN-T5 and GPT-J with Sematic and serve them with Gradio. Read our in-depth article.
            </TypographyDescription>
            <Typography color={"lightGray"}>
            Josh Bauer on July 18, 2023.
            </Typography>
        </BlogWrapper>
        <BlogWrapper >
            <Link target={"_blank"} href="https://www.sematic.dev/blog/how-voxel-cut-model-retraining-from-3-weeks-to-3-days-with-sematic">
            How Voxel cut model retraining time by 80%
            </Link>
            <TypographyDescription>
            Voxel uses Sematic to increase productivity across their Machine Learning (ML) team and retrain Computer Vision models faster. Sematic enabled Voxel to reduce their model turnaround time from 3 weeks to 3 days at a 20x cost saving.
            </TypographyDescription>
            <Typography color={"lightGray"}>
            Emmanuel Turlay on July 5, 2023.
            </Typography>
        </BlogWrapper>
        <BlogWrapper >
            <Link target={"_blank"} href="https://www.sematic.dev/blog/release-notes-0-31-0">
            Release Notes – 0.31.0
            </Link>
            <TypographyDescription>
            Read up on what's new in 0.31.0: GitHub integration, real-time metrics, LLM example, and native dependency packaging.
            </TypographyDescription>
            <Typography color={"lightGray"}>
            Josh Bauer on June 29, 2023.
            </Typography>
        </BlogWrapper>
    </Container>;
}