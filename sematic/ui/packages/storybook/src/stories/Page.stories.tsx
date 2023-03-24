import { Meta, StoryObj } from '@storybook/react';
import { Route, RouterProvider, createRoutesFromElements, createBrowserRouter } from "react-router-dom";
import Shell from "@sematic/common/src/layout/Shell";
import RunDetails from "@sematic/common/src/pages/RunDetails";

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
  render: () => <div style={{margin: "-1em"}}><Router /></div>,
};
