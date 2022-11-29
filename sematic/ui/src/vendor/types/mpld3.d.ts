declare module "mpld3" {
    import { DOMElement } from "react";

    class Figure {}; // please extend as needed 

    export function draw_figure(figid: string, spec: any, 
        process: ((figure: Figure, dom: DOMElement) => void)?,
        clearElem: boolean): Figure;
};
