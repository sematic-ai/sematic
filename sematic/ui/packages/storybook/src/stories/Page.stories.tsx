import React from 'react';
import { Meta, StoryObj } from '@storybook/react';
import Box from "@mui/material/Box";
import { Route, RouterProvider, createRoutesFromElements, createBrowserRouter } from "react-router-dom";
import Shell from "@sematic/common/src/layout/Shell";

const Home = () => {
  return <Box>Empty</Box>
}

const router = createBrowserRouter(
  createRoutesFromElements(
  <Route path="/" element={<Shell />}>
      <Route path="*" element={<Home />} />
  </Route>
));

function Router() {
  return <RouterProvider router={router} />;
}


// More on default export: https://storybook.js.org/docs/react/writing-stories/introduction#default-export
export default {
  title: 'Sematic/Page',
  component: Router,

} as Meta<typeof Router>;

type Story = StoryObj<typeof Router>;

export const Page: Story = {
  render: () => <Router />,
};
