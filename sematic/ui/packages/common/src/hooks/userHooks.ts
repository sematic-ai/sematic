import { UserListPayload } from "@sematic/common/src/ApiContracts";
import { useHttpClient } from "@sematic/common/src/hooks/httpHooks";
import useAsync from "react-use/lib/useAsync";

export type QueryParams = { [key: string]: string };

export function useUsersList() {
    const { fetch } = useHttpClient();
    const state = useAsync(async () => {
        const response = await fetch({
            url: "/api/v1/users"
        });
        return (await response.json() as UserListPayload)["content"];
    }, [fetch]);

    const { loading: isLoading, error, value } = state;

    return { isLoading, error, users: value };
}
