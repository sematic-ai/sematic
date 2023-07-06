import styled from "@emotion/styled";
import theme from "src/theme/new";
import { fontWeightBold } from "src/theme/new/typography";
import { getTypeName } from "src/typeViz/common";
import { RenderDetails } from "src/typeViz/vizMapping";
import { AnyTypeSerialization } from "src/types";
import { useState, useMemo, useCallback, useEffect, Fragment } from "react";
import IconButton from "@mui/material/IconButton";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import { useTheme } from "@mui/material/styles";
import ErrorBoundary from "src/component/ErrorBoundary";
import ImportPath from "src/component/ImportPath";
import { css } from "@emotion/css";


const ContainerBase = styled.div`
    display: flex;
    align-items: center;
    justify-content: space-between;

    padding-left: ${theme.spacing(5)};
    border-left: 1px solid ${theme.palette.p3border.main};
`;

const Container = styled(ContainerBase)`
    min-height: 50px;
    column-gap: ${theme.spacing(2)};
`;

const NestedContainer = styled.div`
    margin-left: ${theme.spacing(5)};

    &.hover {
        > .artifact-row {
            border-left: 1px solid ${theme.palette.primary.main};
        }
    }
`;

const NameType = styled.div`
    flex-shrink: 2;    
    display: flex;
    flex-direction: row;
    overflow: hidden;
    & > span:last-of-type {
        flex-shrink: 1;
        font-size: 12px;
        overflow: hidden;
        color: ${theme.palette.grey[400]};
    }

    & > span:first-of-type {
        flex-shrink: 0;
        font-weight: ${fontWeightBold};
        margin-right: ${theme.spacing(5)}};
    }
`;
const ExpandMoreIconCotainer = styled.span`
    flex-shrink: 0;
`;

const ExpandLessIconCotainer = styled.div`
    width: 100%;
    display: flex;
    justify-content: flex-end;
    margin-bottom: ${theme.spacing(1)};

    & > button {
        transform: translate(50%,0);
        
        svg {
            fill: ${theme.palette.primary.main};
        }
    }
`

const Value = styled.div`
    flex-shrink: 1;
    display: flex;
    flex-direction: row;
    overflow: hidden;
    white-space: nowrap;
    column-gap: ${theme.spacing(2)};
`;

const valueComponentClass = css`
    flex-shrink: 1;
    overflow: hidden;
    text-overflow: ellipsis;
`;

function RenderError({children}: {
    children: React.ReactNode;
}) {
    return <ArtifactExpanderContainer>
        <span style={{color: theme.palette.error.main}}>{children}</span>
    </ArtifactExpanderContainer>
}

export function ArtifactLine(props: { name: string, type?: string, children: React.ReactNode }) {
    const { name, type, children } = props;
    return <Container className={"artifact-row"} style={{ marginRight: "-20px" }}>
        <NameType >
            <span>{name}</span>
            <span>
                <ImportPath>{type}</ImportPath>
            </span>
        </NameType>
        <Value>
            {children}
        </Value>
    </Container>
}

interface ArtifactVizTemplateProps {
    name: string;
    typeSerialization: AnyTypeSerialization;
    valueSummary: any;
    renderDetails: RenderDetails;
    defaultOpen?: boolean;
}

function ArtifactVizTemplate(props: ArtifactVizTemplateProps) {
    const { name, renderDetails, typeSerialization, valueSummary, defaultOpen = false } = props;
    const [open, setOpen] = useState(defaultOpen);

    const { value: ValueComponent, nested: NestedComponent } = renderDetails;

    const hasNested = useMemo(() => !!NestedComponent, [NestedComponent]);

    const type = getTypeName(typeSerialization);

    const toggleOpen = useCallback(() => setOpen(open => !open), [setOpen]);

    const [expandLessHovered, setExpandLessHovered] = useState(false);

    const theme = useTheme();

    const valueComponent = useMemo(() => {
        const component = <ValueComponent open={open} valueSummary={valueSummary}
            typeSerialization={typeSerialization} />;

        if (hasNested) {
            return <span onClick={toggleOpen} style={{ cursor: "pointer" }} className={valueComponentClass}>
                {component}
            </span>;
        }

        return <div style={{marginRight: theme.spacing(8)}} className={valueComponentClass}>
            {component}
        </div>;
    }, [toggleOpen, open, hasNested, theme, ValueComponent, valueSummary, typeSerialization]);

    useEffect(() => {
        if (!open) {
            setExpandLessHovered(false);
        }
    }, [open]);

    return <Fragment key={name}>
        <ArtifactLine name={name} type={type}>
            <ErrorBoundary fallback={<RenderError>Cannot render value</RenderError>}>
                {valueComponent}
            </ErrorBoundary>
            {hasNested && <ExpandMoreIconCotainer>
                <IconButton onClick={toggleOpen} style={{ visibility: open ? "hidden" : "visible" }}>
                    <ExpandMoreIcon />
                </IconButton>
            </ExpandMoreIconCotainer>}
        </ArtifactLine>
        {open && !!NestedComponent && <NestedContainer className={expandLessHovered ? "hover" : ""}>
            <ErrorBoundary fallback={
                <RenderError>
                    Error encountered when rendering the nested representation.
                </RenderError>}>
                <NestedComponent valueSummary={valueSummary} typeSerialization={typeSerialization} />
            </ErrorBoundary>

            <ExpandLessIconCotainer>
                <IconButton onClick={toggleOpen} onMouseEnter={() => setExpandLessHovered(true)}
                    onMouseLeave={() => setExpandLessHovered(false)}>
                    <ExpandLessIcon />
                </IconButton>
            </ExpandLessIconCotainer>
        </NestedContainer>}
    </Fragment>;
}

export function ArtifactInfoContainer(props: { children: React.ReactNode }) {
    return <Container className={"artifact-row"}>
        {props.children}
    </Container>;
}

const ExpanderContainer = styled(ContainerBase)`
    justify-content: flex-end;
`;

export function ArtifactExpanderContainer(props: { children: React.ReactNode }) {
    return <ExpanderContainer className={"artifact-row"}>
        {props.children}
    </ExpanderContainer>;
}

export default ArtifactVizTemplate;
