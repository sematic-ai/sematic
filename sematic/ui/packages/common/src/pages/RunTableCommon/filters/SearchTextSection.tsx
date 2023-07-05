import TextField from "@mui/material/TextField";
import { useAtom } from "jotai";
import { RESET } from "jotai/utils";
import isEmpty from "lodash/isEmpty";
import { forwardRef, useCallback, useImperativeHandle, useState } from "react";
import useEffectOnce from "react-use/lib/useEffectOnce";
import { SectionWithBorder } from "src/component/Section";
import { ResettableHandle } from "src/component/common";
import { searchAtom } from "src/hooks/runHooks";

interface SearchTextSectionProps {
    onSearchChanged?: (search: string) => void;
}

const SearchTextSection = forwardRef<ResettableHandle, SearchTextSectionProps>((props, ref) => {
    const { onSearchChanged } = props;
    const [searchHash] = useAtom(searchAtom);
    const [search, setSearch] = useState<string | typeof RESET>(searchHash);


    const _onSearchChanged = useCallback((search: string) => {
        setSearch(search);
        onSearchChanged?.(search);
    }, [setSearch, onSearchChanged]);

    useImperativeHandle(ref, () => ({
        reset: () => {
            setSearch(RESET);
        }
    }));

    useEffectOnce(() => {
        // Only trigger on mount
        if (!isEmpty(searchHash)) {
            onSearchChanged?.(searchHash);
        }
    });

    return <SectionWithBorder >
        <TextField
            variant="standard"
            fullWidth={true}
            placeholder={"Search..."}
            value={search || ""}
            onChange={(e) => { _onSearchChanged(e.target.value) }}
        />
    </SectionWithBorder>
});

export default SearchTextSection;
