import styled from "@emotion/styled";
import Community from "src/pages/Home/Community";
import Blog from "src/pages/Home/Blog";
import LatestPipelines from "src/pages/Home/latestPipelines";
import LatestRuns from "src/pages/Home/latestRuns";
import theme from "src/theme/new";

const Container = styled.div`
    display: flex;
    flex-direction: column;
    height: 100%;
    width: 100%;

    > div {
        width: 100%;
    }

    #version-check {
        flex-grow: 0;
        flex-shrink: 0;
        height: 50px;
    }

    #main-content {
        flex-grow: 1;
        flex-shrink: 1;
        height: 100%;

        display: flex;
        flex-direction: row;
        
        > div {
            flex-grow: 1;
            flex-shrink: 1;
            flex: 1;
            display: flex;
            flex-direction: column;

            &:first-of-type {
                border-right: 1px solid ${theme.palette.p3border.main};
            }

            > div {
                flex-grow: 1;
                flex-shrink: 1;
                flex: 1;
                padding: 0 ${theme.spacing(5)} ${theme.spacing(2)} ${theme.spacing(5)};
                &:first-of-type {
                    border-bottom: 1px solid ${theme.palette.p3border.main};
                }

                overflow: hidden;
            }
        }
    }

    #latest-runs, #latest-pipelines {
        display: flex;
        flex-direction: column;        
    }
`;

export default function Home() {
    return (
        <Container>
            <div id={"main-content"}>
                <div>
                    <div id={"latest-pipelines"}>
                        <LatestPipelines />
                    </div>
                    <div>
                        <Community />
                    </div>
                </div>
                <div>
                    <div id={"latest-runs"}>
                        <LatestRuns />
                    </div>
                    <div><Blog /></div>
                </div>
            </div>
        </Container>
    );
}
