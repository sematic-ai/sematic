import { ThemeProvider } from "@mui/material/styles";
import RunsDropdownComponent, { RunsDropdownProps } from "@sematic/common/src/component/RunsDropdown";
import theme from "@sematic/common/src/theme/new";
import { Meta, StoryObj } from "@storybook/react";
import CssBaseline from "@mui/material/CssBaseline";
import { Run } from "@sematic/common/src/Models";

export default {
    title: "Sematic/Dropdown",
    component: RunsDropdownComponent,
    decorators: [
        (Story) => (
            <ThemeProvider theme={theme}>
                <CssBaseline />
                <Story />
            </ThemeProvider>
        ),
    ],
} as Meta<StoryProps>;

interface StoryProps extends RunsDropdownProps {
    width: keyof typeof sizeOptions;
    onChange: () => void;
}

const sizeOptions = {
    "200px (small)": 200,
    "400px (medium)": 400,
    "800px (large)": 800
}

const commonArgTypes = {
    width: {
        control: "select", options: Object.keys(sizeOptions)
    },
    onChange: { action: "value changed" }
};

const mockData = [{
    id: "19595830c25e414cb943e1619e8d964c",
    created_at: "2023-04-25T16:29:17.985945+00:00",
    future_state: "RESOLVED"
},
{
    id: "297bafb56a124e27a8dec54850c6a9a2",
    created_at: "2023-05-25T16:29:17.985945+00:00",
    future_state: "CANCELED"
},
{
    id: "c7668586b35f480185768bc83c15d17d",
    created_at: "2022-06-25T16:29:17.985945+00:00",
    future_state: "RAN"
}] as unknown as Array<Run>;

export const RunsDropdown: StoryObj<StoryProps> = {
    render: (props) => {
        const { width, onChange } = props;

        const widthValue = width ? sizeOptions[width] : 200;

        return <div style={{ maxWidth: widthValue }}>
            <RunsDropdownComponent onChange={onChange} runs={mockData} />
        </div>;
    }
};
RunsDropdown.argTypes = commonArgTypes;
