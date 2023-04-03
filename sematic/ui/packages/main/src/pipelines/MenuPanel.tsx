import { BubbleChart, FormatListBulleted, Timeline } from "@mui/icons-material";
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  useTheme,
} from "@mui/material";
import { useRunsTree, useGraphContext } from "../hooks/graphHooks";
import { usePipelinePanelsContext } from "../hooks/pipelineHooks";
import Loading from "../components/Loading";
import RunTree from "./RunTree";

export default function MenuPanel() {
  const { selectedPanelItem, setSelectedPanelItem } = usePipelinePanelsContext();

  const { graph, isLoading } = useGraphContext();

  const runTreeMetaNode = useRunsTree(graph);

  const theme = useTheme();

  let panelList = [
    {
      label: "metrics",
      title: "Pipeline metrics",
      icon: <Timeline />,
      onClick: () => setSelectedPanelItem("metrics"),
    },
    {
      label: "graph",
      title: "Execution graph",
      icon: <BubbleChart />,
      onClick: () => setSelectedPanelItem("graph"),
    },
    {
      label: "run",
      title: "Nested runs",
      icon: <FormatListBulleted />,
      onClick: () => setSelectedPanelItem("run"),
    },
  ];

  return (
    <Box
      sx={{
        gridColumn: 1,
        gridRow: 2,
        backgroundColor: "#f8f9fb",
        borderRight: 1,
        borderColor: theme.palette.grey[200],
        overflowY: "scroll",
      }}
    >
      <List sx={{ py: 0 }}>
        {panelList.map((panel) => (
          <ListItem disablePadding key={panel.label}>
            <ListItemButton
              onClick={panel.onClick}
              sx={{ height: "4em" }}
              selected={selectedPanelItem === panel.label}
            >
              <ListItemIcon sx={{ minWidth: "40px" }}>
                {panel.icon}
              </ListItemIcon>
              <ListItemText primary={panel.title} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <Box
        sx={{
          backgroundColor: "rgba(0,0,0,0.05)",
          WebkitBoxShadow: "inset 0 0 5px rgba(0,0,0,0.1)",
          boxShadow: "inset 0 0 5px rgba(0,0,0,0.1)",
          pt: 3,
        }}
      >
        {!graph && <Loading isLoaded={!isLoading} />}
        {!!runTreeMetaNode && <RunTree runTreeNodes={runTreeMetaNode!.children}/>}
      </Box>
    </Box>
  );
}
