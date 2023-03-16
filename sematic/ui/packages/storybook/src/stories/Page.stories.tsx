import React from 'react';
import { Meta, StoryObj } from '@storybook/react';
import Grid from "@mui/material/Grid";
import { Route, RouterProvider, createRoutesFromElements, createBrowserRouter } from "react-router-dom";
import Shell from "@sematic/common/src/layout/Shell";

const Home = () => {
  return <Grid container spacing={2}>Empty</Grid>
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
