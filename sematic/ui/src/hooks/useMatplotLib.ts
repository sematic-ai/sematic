import * as mpld3 from "mpld3";

export function useMatplotLib(elementId: string) {
    return (spec: any) => {
        mpld3.draw_figure(elementId, spec, null, true);
    };
}
