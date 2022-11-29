import { draw_figure } from "mpld3";

export function useMatplotLib(elementId: string) {
    return (spec: any) => {
        draw_figure(elementId, spec, null, true);
    };
}
