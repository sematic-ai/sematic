import ImportPath from "src/component/ImportPath";
import PipelineTitle from "src/component/PipelineTitle";
import theme from "src/theme/new";
import styled from "@emotion/styled";


const NameSection = styled.div`
    display: flex;
    flex-direction: row;
    column-gap: ${theme.spacing(2)};
    overflow-x: hidden;
    min-width: 100px;
    position: relative;

    & .name {
        flex-grow: 0;
        flex-shrink: 1;
        overflow: hidden;
    }

    & .importPath {
        flex-grow: 1;
        flex-shrink: 9999;
        overflow: hidden;
    }
`;

interface NameColumnProps {
    name: string;
    importPath: string;
}

const NameColumn = (props: NameColumnProps) => {
    const { name, importPath } = props;

    return <NameSection>
        <div className={"name"}>
            <PipelineTitle>{name}</PipelineTitle>
        </div>
        <div className={"importPath"}>
            <ImportPath>{importPath}</ImportPath>
        </div>
    </NameSection>
}

export default NameColumn;
