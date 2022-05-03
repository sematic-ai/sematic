import React from "react";

// Layouts
import DashboardLayout from "./layouts/Dashboard";

// Pages
import RunList from "./pages/RunList";

const routes = [
    {
        path: "/",
        element: <DashboardLayout />,
        children: [
          {
            path: "",
            element: <RunList />,
          },
        ],
    },
    {
        path: "/runs/:id",
        element: <DashboardLayout />,
        children: [
          {
            path: "/runs/:id",
            element: <RunList />,
          },
        ],
    },
];

export default routes;
