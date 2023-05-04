import { SectionWithBorder } from 'src/component/Section';
import TextField from "@mui/material/TextField";


function SearchTextSection() {
    return <SectionWithBorder >
        <TextField
        variant="standard"
        fullWidth={true}
        placeholder={"Search..."}
        />
    </SectionWithBorder>
}

export default SearchTextSection;
