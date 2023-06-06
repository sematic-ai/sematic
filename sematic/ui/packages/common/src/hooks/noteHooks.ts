
import useAsyncRetry from "react-use/lib/useAsyncRetry";
import useAsyncFn from "react-use/lib/useAsyncFn";
import { useHttpClient } from "@sematic/common/src/hooks/httpHooks";
import { NoteCreateRequestPayload, NoteListPayload } from "src/ApiContracts";
import parseJSON from "date-fns/parseJSON";

export function usePipelineNotes(functionPath: string) {
    const {fetch} = useHttpClient();

    const {value, retry, ...others} = useAsyncRetry(async () => {
        const response = await fetch({
            url: `/api/v1/notes?function_path=${functionPath}`
        });
        const notes = (await response.json() as NoteListPayload).content
        notes.sort((a, b) => parseJSON(b.created_at).getTime() - parseJSON(a.created_at).getTime());
        return notes;
    }, [functionPath]);

    return {notes: value, reload: retry, ...others};
}

export function useNoteSubmission() {
    const {fetch} = useHttpClient();

    return useAsyncFn(async (note: NoteCreateRequestPayload) => {
        await fetch({
            url: "/api/v1/notes",
            method: "POST",
            body: note
        });
    }, []);
}
