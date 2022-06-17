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
import { useMemo } from "react";
import { Run } from "../Models";
import RunTree from "./RunTree";

export default function MenuPanel(props: {
  runsById: Map<string, Run>;
  selectedRun: Run;
  selectedPanel: string;
  onPanelSelect: (panel: string) => void;
  onRunSelect: (run: Run) => void;
}) {
  const { runsById, selectedRun, selectedPanel, onPanelSelect, onRunSelect } =
    props;

  const theme = useTheme();

  const runsByParentId = useMemo(() => {
    let map: Map<string | null, Run[]> = new Map();
    Array.from(runsById.values()).forEach((run) => {
      map.set(run.parent_id, [...(map.get(run.parent_id) || []), run]);
    });
    return map;
  }, [runsById]);

  const panelList = [
    {
      label: "graph",
      title: "Execution graph",
      icon: <BubbleChart />,
      onClick: () => onPanelSelect("graph"),
    },
    { label: "topline", title: "Topline metrics", icon: <Timeline /> },
    {
      label: "run",
      title: "Nested runs",
      icon: <FormatListBulleted />,
      onClick: () => {
        onPanelSelect("run");
        onRunSelect(selectedRun);
      },
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
          <ListItem disablePadding>
            <ListItemButton
              onClick={panel.onClick}
              sx={{ height: "4em" }}
              selected={selectedPanel == panel.label}
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
        <RunTree
          runsByParentId={runsByParentId}
          parentId={null}
          selectedRunId={selectedRun?.id}
          onSelectRun={(run) => {
            onPanelSelect("run");
            onRunSelect(run);
          }}
        />
      </Box>
    </Box>
  );
}
