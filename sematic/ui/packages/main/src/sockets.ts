import io from "socket.io-client";

export const jobSocket = io("/job");
