import CssBaseline from "@mui/material/CssBaseline";
import { ThemeProvider } from "@mui/material/styles";
import OwnersFilterSection from "@sematic/common/src/pages/RunTableCommon/filters/OwnersFilterSection";
import StatusFilterSection from "@sematic/common/src/pages/RunSearch/filters/StatusFilterSection";
import UserContext from "@sematic/common/src/context/UserContext";
import { ResettableHandle } from "@sematic/common/src/component/common";
import { useRef } from "@sematic/common/src/reactHooks";
import theme from "@sematic/common/src/theme/new";
import { Meta, StoryObj } from "@storybook/react";

export default {
    title: "Sematic/RunFilters",
    decorators: [
        (Story) => (
            <ThemeProvider theme={theme}>
                <CssBaseline />
                <Story />
            </ThemeProvider>
        ),
    ],
} as Meta<StoryProps>;

interface StoryProps {
    onFilterChange: (filters: string[]) => void;
}

const commonArgTypes = {
    onFilterChange: { action: "filter change" },
};

function StatusFilterStory(props: StoryProps) {
    const ref = useRef<ResettableHandle>(null);
    const { onFilterChange } = props;

    return <div style={{ width: "300px" }}>
        <StatusFilterSection ref={ref} onFiltersChanged={onFilterChange} />
        <button onClick={() => { ref.current?.reset()}} >Clear</button>
    </div>;
}

export const StatusFilter: StoryObj<StoryProps> = {
    render: (props) => {
        return <StatusFilterStory {...props} />;
    },
    argTypes: commonArgTypes
};

function OwnerFilterStory(props: StoryProps) {
    const ref = useRef<ResettableHandle>(null);
    const { onFilterChange } = props;

    return <div style={{ width: "300px" }}>
        <UserContext.Provider value={{ user: { id: "1", name: "test" }} as any}>
            <OwnersFilterSection ref={ref} onFiltersChanged={onFilterChange} />
        </UserContext.Provider>
        <button onClick={() => { ref.current?.reset()}} >Clear</button>
    </div>;
}

export const OwnerFilter: StoryObj<StoryProps> = {
    render: (props) => {
        return <OwnerFilterStory {...props} />;
    },
    argTypes: commonArgTypes
};
