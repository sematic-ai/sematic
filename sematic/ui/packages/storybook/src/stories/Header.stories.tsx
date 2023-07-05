import { ThemeProvider } from "@mui/material/styles";
import Menu from "@sematic/common/src/component/menu";
import theme from "@sematic/common/src/theme/new";
import { Meta, StoryObj } from "@storybook/react";
import { Route, createBrowserRouter, createRoutesFromElements, RouterProvider } from "react-router-dom";
import { ReactElement } from "react";

export default {
    title: "Sematic/Header",
    component: Menu,
    decorators: [
        (Story) => (
            <ThemeProvider theme={theme}>
                <Story />
            </ThemeProvider>
        ),
    ],
} as Meta<StoryProps>;

interface StoryProps {
    selectedItem: string;
}

const dummyRouter = (node: ReactElement) => createBrowserRouter(
    createRoutesFromElements(
        <Route path="*" index element={node} />
    ));

export const Header: StoryObj<StoryProps> = {
    render: (props) => {
        const { selectedItem } = props;

        const router = dummyRouter(
            <Menu selectedKey={selectedItem} />
        );

        return <RouterProvider router={router} />;
    },
    argTypes: {
        selectedItem: {
            control: "select",
            options: [
                undefined, "runs", "pipelines", "metrics"
            ]
        }
    }
};

