import Shell from "@sematic/common/src/layout/Shell";
import RunDetails from "@sematic/common/src/pages/RunDetails";
import { Meta, StoryObj } from '@storybook/react';
import { createBrowserRouter, createRoutesFromElements, Route, RouterProvider } from "react-router-dom";

const router = createBrowserRouter(
  createRoutesFromElements(
    <Route path="/" element={<Shell />}>
      <Route path="*" element={<RunDetails />} />
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

  parameters : {
    layout: 'fullscreen' 
  }
};
