import { Children, ReactNode, createContext } from "react";
import Fill from "./Fill";
import * as mitt from "mitt";

export type Name = string | Symbol;
export type Listener = (components: Component[]) => void;

export interface Component {
    name: Name;
    fill: Fill;
    children: Exclude<ReactNode, boolean | null | undefined>;
}

export interface FillRegistration {
    listeners: Listener[];
    components: Component[];
}

export interface Db {
    byName: Map<Name, FillRegistration>;
    byFill: Map<Fill, Component>;
}

type Events = {
    "fill-mount": { fill: Fill };
    "fill-updated": { fill: Fill };
    "fill-unmount": { fill: Fill };
};



export default class Manager {
    private _bus: mitt.Emitter<Events>;
    private _db: Db;

    constructor(bus: mitt.Emitter<Events>) {
        this._bus = bus;

        this.handleFillMount = this.handleFillMount.bind(this);
        this.handleFillUpdated = this.handleFillUpdated.bind(this);
        this.handleFillUnmount = this.handleFillUnmount.bind(this);

        this._db = {
            byName: new Map(),
            byFill: new Map()
        };
    }

    mount() {
        this._bus.on("fill-mount", this.handleFillMount);
        this._bus.on("fill-updated", this.handleFillUpdated);
        this._bus.on("fill-unmount", this.handleFillUnmount);
    }

    unmount() {
        this._bus.off("fill-mount", this.handleFillMount);
        this._bus.off("fill-updated", this.handleFillUpdated);
        this._bus.off("fill-unmount", this.handleFillUnmount);
    }

    handleFillMount({ fill }: { fill: Fill }) {
        const children = Children.toArray(fill.props.children);
        const name = fill.props.name;
        const component = { fill, children: children, name };

        // If the name is already registered
        const reg = this._db.byName.get(name);

        if (reg) {
            reg.components.push(component);

            // notify listeners
            reg.listeners.forEach(fn => fn(reg.components));
        } else {
            this._db.byName.set(name, {
                listeners: [],
                components: [component]
            });
        }

        this._db.byFill.set(fill, component);
    }

    handleFillUpdated({ fill }: { fill: Fill }) {
        // Find the component
        const component = this._db.byFill.get(fill);

        // Get the new elements
        const newElements = Children.toArray(fill.props.children);

        if (component) {
            // replace previous element with the new one
            component.children = newElements;

            const name = component.name;

            // notify listeners
            const reg = this._db.byName.get(name);

            if (reg) {
                reg.listeners.forEach(fn => fn(reg.components));
            } else {
                throw new Error("registration was expected to be defined");
            }
        } else {
            throw new Error("component was expected to be defined");
        }
    }

    handleFillUnmount({ fill }: { fill: Fill }) {
        const oldComponent = this._db.byFill.get(fill);

        if (!oldComponent) {
            throw new Error("component was expected to be defined");
        }

        const name = oldComponent.name;
        const reg = this._db.byName.get(name);

        if (!reg) {
            throw new Error("registration was expected to be defined");
        }

        const components = reg.components;

        // remove previous component
        components.splice(components.indexOf(oldComponent), 1);

        // Clean up byFill reference
        this._db.byFill.delete(fill);

        if (reg.listeners.length === 0 &&
            reg.components.length === 0) {
            this._db.byName.delete(name);
        } else {
            // notify listeners
            reg.listeners.forEach(fn => fn(reg.components));
        }
    }

    /**
     * Triggers once immediately, then each time the components change for a location
     *
     * name: String, fn: (components: Component[]) => void
     */
    onComponentsChange(name: Name, fn: Listener) {
        const reg = this._db.byName.get(name);

        if (reg) {
            reg.listeners.push(fn);
            fn(reg.components);
        } else {
            this._db.byName.set(name, {
                listeners: [fn],
                components: []
            });
            fn([]);
        }
    }

    getFillsByName(name: string): Fill[] {
        const registration = this._db.byName.get(name);

        if (!registration) {
            return [];
        } else {
            return registration.components.map(c => c.fill);
        }
    }

    getChildrenByName(name: string): Array<ReactNode> {
        const registration = this._db.byName.get(name);

        if (!registration) {
            return [];
        } else {
            return registration.components
                .map(component => component.children)
                .reduce<Array<ReactNode>>((acc, memo) => acc.concat(memo), []);
        }
    }

    /**
     * Removes previous listener
     *
     * name: String, fn: (components: Component[]) => void
     */
    removeOnComponentsChange(name: Name, fn: Listener) {
        const reg = this._db.byName.get(name);

        if (!reg) {
            throw new Error("expected registration to be defined");
        }

        const listeners = reg.listeners;
        listeners.splice(listeners.indexOf(fn), 1);
    }
}

export const SlotFillContext = createContext<{
    manager: Manager;
    bus: mitt.Emitter<Events>;
}>(null as any)
