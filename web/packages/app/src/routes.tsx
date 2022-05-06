import React from "react";

// Layouts
import DashboardLayout from "./layouts/Dashboard";

// Pages
import Runs from "./pages/Runs/Runs";
import RunDetails from "./pages/Runs/RunDetails";
import Discover from "./pages/Discover";

const routes = [
    {
      path: "/",
      element: <DashboardLayout />,
      children: [
        {
          path: "",
          element: <Discover />,
        },
      ],
    },
    {
        path: "/runs",
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
            element: <RunDetails />,
          },
        ],
    },
    {
      path: "/types",
      element: <DashboardLayout />,
      children: [
        {
          path: "",
          element: <RunDetails />,
        },
      ],
  },
];

export default routes;
