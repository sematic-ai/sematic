import * as React from "react";
import mitt, { Emitter } from "mitt";


import Manager, { SlotFillContext } from "./Manager";
import Fill from "./Fill";

export type Events = {
    "fill-mount": { fill: Fill };
    "fill-updated": { fill: Fill };
    "fill-unmount": { fill: Fill };
};


export default class Provider extends React.Component<any, any> {
    private _bus: Emitter<Events>;
    private _manager: Manager;

    constructor(props: {}) {
        super(props);
        this._bus = mitt();
        this._manager = new Manager(this._bus);
        this._manager.mount();
    }

    componentWillUnmount() {
        this._manager.unmount();
    }

    render(): any {
        return React.createElement(SlotFillContext.Provider, {
            value: {
                manager: this._manager,
                bus: this._bus
            }
        }, this.props.children);        
    }

    /**
     * Returns instances of Fill react components
     */
    getFillsByName(name: string): Fill[] {
        return this._manager.getFillsByName(name);
    }

    /**
     * Return React elements that were inside Fills
     */
    getChildrenByName(name: string): Array<React.ReactNode> {
        return this._manager.getChildrenByName(name);
    }
}