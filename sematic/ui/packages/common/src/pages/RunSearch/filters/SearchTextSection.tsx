import TextField from "@mui/material/TextField";
import { forwardRef, useCallback, useImperativeHandle, useState } from "react";
import { SectionWithBorder } from "src/component/Section";
import { ResettableHandle } from "src/component/common";

interface SearchTextSectionProps {
    onSearchChanged?: (search: string) => void;
}

const SearchTextSection = forwardRef<ResettableHandle, SearchTextSectionProps>((props, ref) => {
    const { onSearchChanged } = props;    
    const [search, setSearch] = useState<string>("");

    const _onSearchChanged = useCallback((search: string) => {
        setSearch(search);
        onSearchChanged?.(search);
    }, [onSearchChanged]);

    useImperativeHandle(ref, () => ({
        reset: () => {
            setSearch("");
        }
    }));
    
    return <SectionWithBorder >
        <TextField
            variant="standard"
            fullWidth={true}
            placeholder={"Search..."}
            value={search}
            onChange={(e) => {_onSearchChanged(e.target.value)}}
        />
    </SectionWithBorder>
});

export default SearchTextSection;
