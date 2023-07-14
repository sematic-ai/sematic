import * as React from "react";
import { SlotFillContext } from "./Manager";

export interface Props {
    name: string | Symbol;
    [key: string]: any;
}

export default class Fill extends React.Component<Props, {}> {
    static contextType = SlotFillContext;
    
    componentDidMount() {
        (this.context as React.ContextType<typeof SlotFillContext>).bus.emit("fill-mount", {
            fill: this
        });
    }

    componentDidUpdate() {
        (this.context as React.ContextType<typeof SlotFillContext>).bus.emit("fill-updated", {
            fill: this
        });
    }

    componentWillUnmount() {
        (this.context as React.ContextType<typeof SlotFillContext>).bus.emit("fill-unmount", {
            fill: this
        });
    }

    render() {
        return null;
    }
}