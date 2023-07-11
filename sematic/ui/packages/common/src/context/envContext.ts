import React from "react";

const EnvContext = React.createContext<Map<string, string>>(new Map());

export default EnvContext;
