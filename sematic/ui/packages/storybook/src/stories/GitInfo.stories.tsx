import { ThemeProvider } from "@mui/material/styles";
import { GitInfoBoxPresentation } from "@sematic/common/src/component/GitInfo";
import theme from "@sematic/common/src/theme/new";
import { Meta, StoryObj } from "@storybook/react";
import CssBaseline from "@mui/material/CssBaseline";
import SnackBarProvider from "@sematic/common/src/context/SnackBarProvider";

export default {
    title: "Sematic/GitInfo",
    component: GitInfoBoxPresentation,
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
    ["has uncommited changes"]: boolean;
    onCopied: () => void;
}


export const GitInfo: StoryObj<StoryProps> = {
    render: (props) => {
        const { "has uncommited changes": hasUncommitedChanges,
            onCopied } = props;

        return <SnackBarProvider setSnackMessageOverride={onCopied}>
            <GitInfoBoxPresentation hasUncommittedChanges={hasUncommitedChanges}
                branch={"acme/feature-branch"} commit="pf49df3890abcdef" />
        </SnackBarProvider>
    },
    argTypes: {
        "has uncommited changes": { control: "boolean" },
        onCopied: { action: "onCopied" }
    }
};

