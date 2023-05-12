import Shell from "@sematic/common/src/layout/Shell";
import RunDetailsComponent from "@sematic/common/src/pages/RunDetails";
import { Meta, StoryObj } from '@storybook/react';
import { Route, RouterProvider, createBrowserRouter, createRoutesFromElements } from "react-router-dom";

const runDetailsRouter = createBrowserRouter(
  createRoutesFromElements(
    <Route path="/" element={<Shell />}>
      <Route path="*" element={<RunDetailsComponent />} />
    </Route>
  ));

function RunDetailsRouter() {
  return <RouterProvider router={runDetailsRouter} />;
}


// More on default export: https://storybook.js.org/docs/react/writing-stories/introduction#default-export
export default {
  title: 'Sematic/Page',
  component: RunDetailsRouter,

} as Meta<typeof RunDetailsRouter>;

export const RunDetails: StoryObj<typeof RunDetailsRouter> = {
  render: () => <RunDetailsRouter />,

  parameters : {
    layout: 'fullscreen' 
  }
};
