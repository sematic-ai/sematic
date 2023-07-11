import { atom } from "jotai";
import { selectedRunAtom } from "src/pages/RunDetails";
export const selectedRun = atom((get) => get(selectedRunAtom))

