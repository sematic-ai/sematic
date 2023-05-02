import React from "react";
import { User } from "src/Models";

const UserContext = React.createContext<{
    user: User | null;
    signOut: (() => void) | null;
}>({ user: null, signOut: null });

export default UserContext;
