import React from "react";

// Layouts
import DashboardLayout from "./layouts/Dashboard";

// Pages
import Runs from "./pages/Runs/Runs";

const routes = [
    {
        path: "/",
        element: <DashboardLayout />,
        children: [
          {
            path: "",
            element: <Runs />,
          },
        ],
    },
    {
        path: "/runs/:id",
        element: <DashboardLayout />,
        children: [
          {
            path: "",
            element: <Runs />,
          },
        ],
    },
];

export default routes;
