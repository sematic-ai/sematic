import * as React from "react";
import Fill from "./Fill";
import Manager, { Component, SlotFillContext } from "./Manager";

export interface Props {
    /**
     * The name of the component. Use a symbol if you want to be 100% sue the Slot
     * will only be filled by a component you create
     */
    name: string | Symbol;

    /**
     * Props to be applied to the child Element of every fill which has the same name.
     *
     *  If the value is a function, it must have the following signature:
     *    (target: Fill, fills: Fill[]) => void;
     *
     *  This allows you to access props on the fill which invoked the function
     *  by using target.props.something()
     */
    fillChildProps?: { [key: string]: any };

    children?: React.ReactNode;
}

export interface State {
    components: Component[];
}

export interface Context {
    manager: Manager;
}

export default class Slot extends React.Component<Props, State> {
    static contextType = SlotFillContext;

    constructor(props: Props) {
        super(props);
        this.state = { components: [] };
        this.handleComponentChange = this.handleComponentChange.bind(this);
    }

    UNSAFE_componentWillMount() {
        (this.context as React.ContextType<typeof SlotFillContext>).manager.onComponentsChange(this.props.name, this.handleComponentChange);
    }

    handleComponentChange(components: Component[]) {
        this.setState({ components });
    }

    get fills(): Fill[] {
        return this.state.components.map(c => c.fill);
    }

    componentDidUpdate(prevProps: Props) {
        if (this.props.name !== prevProps.name) {
            (this.context as React.ContextType<typeof SlotFillContext>).manager
                .removeOnComponentsChange(this.props.name, this.handleComponentChange);

            const name = this.props.name;

            (this.context as React.ContextType<typeof SlotFillContext>).manager
                .onComponentsChange(name, this.handleComponentChange);
        }
    }

    componentWillUnmount() {
        const name = this.props.name;
        (this.context as React.ContextType<typeof SlotFillContext>).manager.removeOnComponentsChange(name, this.handleComponentChange);
    }

    render() {
        const aggElements: React.ReactNode[] = [];

        this.state.components.forEach((component, index) => {
            const { fill, children } = component;
            const { fillChildProps } = this.props;

            if (fillChildProps) {
                const transform = (acc: Record<string, any>, key: string) => {
                    const value = fillChildProps[key];

                    if (typeof value === "function") {
                        acc[key] = () => value(fill, this.fills);
                    } else {
                        acc[key] = value;
                    }

                    return acc;
                };

                const fillChildProps2 = Object.keys(fillChildProps).reduce(transform, {});

                const chilrenArray = React.Children.toArray(children);
                chilrenArray.forEach((child, index2) => {
                    if (typeof child === "number" || typeof child === "string") {
                        throw new Error("Only element children will work here");
                    }
                    aggElements.push(
                        React.cloneElement(child as React.ReactElement, 
                            { key: index.toString() + index2.toString(), ...fillChildProps2 })
                    );
                });
            } else {
                const chilrenArray = React.Children.toArray(children);

                chilrenArray.forEach((child, index2) => {
                    if (typeof child === "number" || typeof child === "string") {
                        throw new Error("Only element children will work here");
                    }

                    aggElements.push(
                        React.cloneElement(child as React.ReactElement, { key: index.toString() + index2.toString() })
                    );
                });
            }
        });

        if (typeof this.props.children === "function") {
            const element = (this.props.children as Function)(aggElements);

            if (React.isValidElement(element) || element === null) {
                return element;
            } else {
                const untypedThis: any = this;
                const parentConstructor = untypedThis._reactInternalInstance._currentElement._owner._instance.constructor;
                const displayName = parentConstructor.displayName || parentConstructor.name;
                const message = "Slot rendered with function must return a valid React " +
                    `Element. Check the ${displayName} render function.`;
                throw new Error(message);
            }
        } else {
            return aggElements;
        }
    }
}