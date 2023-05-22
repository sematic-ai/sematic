import { updateHash } from "@sematic/common/src/utils/url";
import { useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";

export default function useHashUpdater() {
    const { hash } = useLocation();
    const navigate = useNavigate();

    return useCallback((
        hashOverrideValues: Record<string, string | Symbol>, replace: boolean = false) => {
        let newHashValue = hash.replace(/^#/, "");

        newHashValue = updateHash(newHashValue, hashOverrideValues);

        navigate({
            hash: newHashValue
        }, {
            replace
        });
    }, [hash, navigate]);
}
