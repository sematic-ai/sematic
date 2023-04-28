import TextField from "@mui/material/TextField";
import CollapseableFilterSection from 'src/pages/RunSearch/filters/CollapseableFilterSection';
import styled from '@emotion/styled';
import theme from "src/theme/new";

const Container = styled.div`
    margin: -${theme.spacing(2.4)} 0;
    height: 50px;
    flex-direction: column;
    justify-content: center;
    display: flex;
`;

const TagsFilterSection = () => {
    return <CollapseableFilterSection title={"Tags"} >
        <Container>
            <TextField
                variant="standard"
                fullWidth={true}
                placeholder={"Tags..."}
            />
        </Container>
    </CollapseableFilterSection>;
}

export default TagsFilterSection;
