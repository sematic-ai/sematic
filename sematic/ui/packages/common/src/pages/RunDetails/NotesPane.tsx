import styled from "@emotion/styled";
import { useCallback, useContext, useRef } from "react";
import { Run, User } from "src/Models";
import Note from "src/component/Note";
import RootRunContext, { useRootRunContext } from "src/context/RootRunContext";
import { useRunDetailsSelectionContext } from "src/context/RunDetailsSelectionContext";
import UserContext from "src/context/UserContext";
import { useNoteSubmission, usePipelineNotes } from "src/hooks/noteHooks";
import SubmitNoteSection from "src/pages/RunDetails/SubmitNoteSection";
import theme from "src/theme/new";
import { ExtractContextType } from "src/utils/typings";

const Notes = styled.section`
    flex-grow: 1;
    flex-shrink: 1;
    overflow-y: auto;
    overflow-x: hidden;
    scrollbar-gutter: stable;
    margin-right: -${theme.spacing(2.4)};
    margin-left: -${theme.spacing(2.4)};
`;

function getUserName(user: User | null): string {
    return (!!user && user.first_name) || "Anonymous";
}

const NotesPane = () => {
    const { rootRun, isGraphLoading } = useRootRunContext() as ExtractContextType<typeof RootRunContext> & {
        rootRun: Run;
    };
    const { selectedRun } = useRunDetailsSelectionContext();
    const { user } = useContext(UserContext);

    const { notes, reload: reloadNotes } = usePipelineNotes(rootRun.function_path);
    const [, submitNoteToServer] = useNoteSubmission();

    const isSubmitting = useRef(false);

    const onSubmit = useCallback(async (content: string) => {
        if (isSubmitting.current || isGraphLoading) {
            return;
        }
        isSubmitting.current = true;

        await submitNoteToServer({
            note: {
                author_id: user?.email || "anonymous@acme.com",
                note: content,
                root_id: rootRun.id,
                run_id: selectedRun!.id,
            }
        });

        isSubmitting.current = false;
        reloadNotes();
    }, [submitNoteToServer, user, isGraphLoading, selectedRun, reloadNotes, rootRun.id]);

    return <>
        <SubmitNoteSection onSubmit={onSubmit} />
        <Notes>
            {(notes || []).map(({ note, run_id, created_at, user }, index) =>
                <Note key={index} content={note} name={getUserName(user)} runId={run_id}
                    createdAt={created_at as unknown as string} />)}
        </Notes>
    </>;
}

export default NotesPane;
