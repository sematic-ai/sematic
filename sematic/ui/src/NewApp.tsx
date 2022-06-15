import {
  BatchPrediction,
  BubbleChart,
  ChatBubbleOutlined,
  ChevronLeft,
  FormatListBulleted,
  Timeline,
} from "@mui/icons-material";
import {
  Box,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  lighten,
  Link,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import { ThemeProvider } from "@mui/material/styles";
import createTheme from "./themes/mira";
import { SiDiscord, SiReadthedocs } from "react-icons/si";
import CalculatorPath from "./components/CalculatorPath";
import RunStateChip from "./components/RunStateChip";
import { Outlet } from "react-router-dom";

export function SideBar() {
  const theme = useTheme();

  return (
    <Box
      sx={{
        display: "grid",
        gridTemplateRows: "auto 1fr auto",
        gridTemplateColumns: "auto",
        backgroundColor: theme.palette.grey[800],
        color: "rgba(255, 255, 255, 0.5)",
        textAlign: "center",
        height: "100vh",
      }}
    >
      <Stack sx={{ gridRow: 1, spacing: 2, paddingTop: 3 }}>
        <Box sx={{ color: "#ffffff", paddingBottom: 4 }}>
          <Typography fontSize={32}>🦊</Typography>
        </Box>
        <Box>
          <Link
            href="/new/pipelines"
            sx={{ color: "rgba(255, 255, 255, 0.5)" }}
            underline="none"
          >
            <BatchPrediction fontSize="large" />
            <Typography fontSize={10}>Pipelines</Typography>
          </Link>
        </Box>
      </Stack>
      <Stack
        spacing={4}
        sx={{
          gridRow: 3,
          fontSize: 24,
          paddingBottom: 4,
        }}
      >
        <Box>
          <SiReadthedocs />
          <Typography fontSize={10}>Docs</Typography>
        </Box>
        <Box>
          <SiDiscord />
          <Typography fontSize={10}>Discord</Typography>
        </Box>
      </Stack>
    </Box>
  );
}

export function Shell() {
  const theme = useTheme();
  return (
    <ThemeProvider theme={createTheme("LIGHT")}>
      <Box
        sx={{
          height: "100vh",
          display: "grid",
          gridTemplateColumns: "60px auto",
          gridTemplateRows: "1fr",
        }}
      >
        <Box sx={{ gridColumn: 1, gridRow: 1 }}>
          <SideBar />
        </Box>
        <Box sx={{ gridColumn: 2 }}>
          <Outlet />
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default function NewApp() {
  const theme = useTheme();

  const backgroundColor = "#f8f9fb";
  const borderColor = "#f0f0f0";

  return (
    <ThemeProvider theme={createTheme("LIGHT")}>
      <Box
        sx={{
          display: "grid",
          height: "100vh",
          gridTemplateColumns: "55px 200px 1fr 250px",
          gridTemplateRows: "70px 1fr",
        }}
      >
        <Box
          sx={{
            gridColumn: 1,
            gridRow: "1 / 3",
            display: "grid",
            gridTemplateRows: "auto 1fr auto",
            gridTemplateColumns: "auto",
            backgroundColor: theme.palette.grey[800],
            color: "rgba(255, 255, 255, 0.5)",
            textAlign: "center",
          }}
        >
          <Stack sx={{ gridRow: 1, spacing: 2, paddingTop: 3 }}>
            <Box sx={{ color: "#ffffff", paddingBottom: 4 }}>
              <Typography fontSize={32}>🦊</Typography>
            </Box>
            <Box>
              <BatchPrediction fontSize="large" />
              <Typography fontSize={10}>Pipelines</Typography>
            </Box>
          </Stack>
          <Stack
            spacing={4}
            sx={{
              gridRow: 3,
              fontSize: 24,
              paddingBottom: 4,
            }}
          >
            <Box>
              <SiReadthedocs />
              <Typography fontSize={10}>Docs</Typography>
            </Box>
            <Box>
              <SiDiscord />
              <Typography fontSize={10}>Discord</Typography>
            </Box>
          </Stack>
        </Box>
        <Box
          sx={{
            gridColumn: "2 / 5",
            gridRow: 1,
            //backgroundColor: backgroundColor,
            display: "grid",
            gridTemplateColumns: "70px 1fr auto",
            borderBottom: 1,
            borderColor: borderColor,
          }}
        >
          <Box
            sx={{
              gridColumn: 1,
              textAlign: "center",
              paddingTop: 2,
              borderRight: 1,
              borderColor: borderColor,
              marginY: 3,
            }}
          >
            <ChevronLeft fontSize="large" />
          </Box>
          <Box sx={{ gridColumn: 2, pt: 3, pl: 7 }}>
            <Typography variant="h4">PyTorch MNIST example</Typography>
            <CalculatorPath calculatorPath="sematic.examples.mnist.pytorch.pipeline.pipeline" />
          </Box>
          <Box
            sx={{
              gridColumn: 3,
              marginY: 3,
              borderLeft: 1,
              borderColor: borderColor,
              paddingX: 10,
              paddingTop: 1,
            }}
          >
            <FormControl fullWidth size="small">
              <InputLabel id="demo-simple-select-label">Latest runs</InputLabel>
              <Select
                labelId="demo-simple-select-label"
                id="demo-simple-select"
                value={10}
                label="Latest runs"
                //onChange={handleChange}
              >
                <MenuItem value={10}>
                  <Typography
                    component="span"
                    sx={{ display: "flex", alignItems: "center" }}
                  >
                    <RunStateChip state="RESOLVED" />
                    <Box mx={3}>27 minutes &middot; 3 minutes ago</Box>
                  </Typography>
                </MenuItem>
                <MenuItem value={20}>Twenty</MenuItem>
                <MenuItem value={30}>Thirty</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Box>
        <Box
          sx={{
            gridColumn: 2,
            gridRow: 2,
            backgroundColor: backgroundColor,
            borderRight: 1,
            borderColor: borderColor,
          }}
        >
          <List>
            <ListItem disablePadding>
              <ListItemButton sx={{ height: "4em" }}>
                <ListItemIcon sx={{ minWidth: "40px" }}>
                  <BubbleChart />
                </ListItemIcon>
                <ListItemText primary="Execution graph" />
              </ListItemButton>
            </ListItem>
            <ListItem disablePadding>
              <ListItemButton sx={{ height: "4em" }}>
                <ListItemIcon sx={{ minWidth: "40px" }}>
                  <Timeline />
                </ListItemIcon>
                <ListItemText primary="Topline metrics" />
              </ListItemButton>
            </ListItem>
            <ListItem sx={{ height: "4em" }}>
              <ListItemIcon sx={{ minWidth: "40px" }}>
                <FormatListBulleted />
              </ListItemIcon>
              <ListItemText primary="Nested runs" />
            </ListItem>
          </List>
        </Box>
        <Box sx={{ gridColumn: 3, gridRow: 2, overflowY: "scroll", p: 10 }}>
          Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do
          eiusmod tempor incididunt ut labore et dolore magna aliqua. Semper
          auctor neque vitae tempus quam pellentesque nec nam aliquam. Semper
          eget duis at tellus. Nec sagittis aliquam malesuada bibendum arcu
          vitae elementum curabitur vitae. Sit amet nisl suscipit adipiscing
          bibendum est ultricies. Ac turpis egestas sed tempus urna. Blandit
          aliquam etiam erat velit scelerisque in dictum. Quam viverra orci
          sagittis eu volutpat odio. Arcu cursus vitae congue mauris rhoncus
          aenean vel elit. Parturient montes nascetur ridiculus mus mauris vitae
          ultricies leo integer. Etiam non quam lacus suspendisse faucibus
          interdum posuere lorem. Odio euismod lacinia at quis risus. Commodo
          sed egestas egestas fringilla phasellus faucibus scelerisque eleifend.
          Ut ornare lectus sit amet est. Quis ipsum suspendisse ultrices gravida
          dictum. Rhoncus urna neque viverra justo nec ultrices dui sapien eget.
          Imperdiet nulla malesuada pellentesque elit eget gravida cum sociis.
          Proin sed libero enim sed faucibus turpis in eu. Et sollicitudin ac
          orci phasellus egestas. Eget dolor morbi non arcu risus quis. Felis
          eget velit aliquet sagittis id consectetur purus ut. Velit sed
          ullamcorper morbi tincidunt ornare. Facilisis magna etiam tempor orci
          eu. Facilisi nullam vehicula ipsum a arcu cursus. Magna fringilla urna
          porttitor rhoncus. Justo donec enim diam vulputate ut pharetra sit.
          Senectus et netus et malesuada fames ac turpis egestas. Amet
          consectetur adipiscing elit duis tristique sollicitudin nibh. Arcu
          vitae elementum curabitur vitae nunc sed velit dignissim sodales.
          Purus viverra accumsan in nisl nisi. Quisque id diam vel quam.
          Ultrices sagittis orci a scelerisque purus semper eget duis at.
          Facilisi cras fermentum odio eu feugiat pretium. Ut morbi tincidunt
          augue interdum velit euismod in. Et tortor consequat id porta nibh
          venenatis cras sed. Adipiscing diam donec adipiscing tristique risus
          nec feugiat in fermentum. Non curabitur gravida arcu ac tortor
          dignissim convallis aenean et. Erat pellentesque adipiscing commodo
          elit. Rutrum tellus pellentesque eu tincidunt tortor aliquam nulla
          facilisi cras. Nunc id cursus metus aliquam eleifend. Justo nec
          ultrices dui sapien eget. Elementum pulvinar etiam non quam lacus
          suspendisse faucibus. Nibh mauris cursus mattis molestie a iaculis at.
          Urna nec tincidunt praesent semper feugiat. Est velit egestas dui id.
          Lobortis elementum nibh tellus molestie nunc non blandit. Tristique
          senectus et netus et malesuada fames ac. Sit amet risus nullam eget
          felis. Elementum pulvinar etiam non quam lacus suspendisse faucibus.
          Sit amet luctus venenatis lectus magna fringilla urna porttitor.
          Laoreet id donec ultrices tincidunt arcu non. Adipiscing elit duis
          tristique sollicitudin. Habitant morbi tristique senectus et. Turpis
          nunc eget lorem dolor. Accumsan lacus vel facilisis volutpat est velit
          egestas. Bibendum est ultricies integer quis auctor elit sed
          vulputate. Molestie at elementum eu facilisis sed odio morbi. Cursus
          turpis massa tincidunt dui ut ornare lectus sit. Egestas tellus rutrum
          tellus pellentesque eu tincidunt tortor. Adipiscing diam donec
          adipiscing tristique. At in tellus integer feugiat scelerisque varius
          morbi enim nunc. Risus pretium quam vulputate dignissim suspendisse.
          Amet nisl purus in mollis nunc. Non quam lacus suspendisse faucibus
          interdum posuere lorem. Urna cursus eget nunc scelerisque. In
          hendrerit gravida rutrum quisque. Adipiscing bibendum est ultricies
          integer quis auctor elit sed. Blandit turpis cursus in hac habitasse
          platea dictumst quisque. Diam vel quam elementum pulvinar etiam non
          quam. Scelerisque varius morbi enim nunc faucibus a pellentesque.
          Mauris cursus mattis molestie a iaculis at erat. Arcu ac tortor
          dignissim convallis aenean et tortor at. Lorem ipsum dolor sit amet,
          consectetur adipiscing elit, sed do eiusmod tempor incididunt ut
          labore et dolore magna aliqua. Semper auctor neque vitae tempus quam
          pellentesque nec nam aliquam. Semper eget duis at tellus. Nec sagittis
          aliquam malesuada bibendum arcu vitae elementum curabitur vitae. Sit
          amet nisl suscipit adipiscing bibendum est ultricies. Ac turpis
          egestas sed tempus urna. Blandit aliquam etiam erat velit scelerisque
          in dictum. Quam viverra orci sagittis eu volutpat odio. Arcu cursus
          vitae congue mauris rhoncus aenean vel elit. Parturient montes
          nascetur ridiculus mus mauris vitae ultricies leo integer. Etiam non
          quam lacus suspendisse faucibus interdum posuere lorem. Odio euismod
          lacinia at quis risus. Commodo sed egestas egestas fringilla phasellus
          faucibus scelerisque eleifend. Ut ornare lectus sit amet est. Quis
          ipsum suspendisse ultrices gravida dictum. Rhoncus urna neque viverra
          justo nec ultrices dui sapien eget. Imperdiet nulla malesuada
          pellentesque elit eget gravida cum sociis. Proin sed libero enim sed
          faucibus turpis in eu. Et sollicitudin ac orci phasellus egestas. Eget
          dolor morbi non arcu risus quis. Felis eget velit aliquet sagittis id
          consectetur purus ut. Velit sed ullamcorper morbi tincidunt ornare.
          Facilisis magna etiam tempor orci eu. Facilisi nullam vehicula ipsum a
          arcu cursus. Magna fringilla urna porttitor rhoncus. Justo donec enim
          diam vulputate ut pharetra sit. Senectus et netus et malesuada fames
          ac turpis egestas. Amet consectetur adipiscing elit duis tristique
          sollicitudin nibh. Arcu vitae elementum curabitur vitae nunc sed velit
          dignissim sodales. Purus viverra accumsan in nisl nisi. Quisque id
          diam vel quam. Ultrices sagittis orci a scelerisque purus semper eget
          duis at. Facilisi cras fermentum odio eu feugiat pretium. Ut morbi
          tincidunt augue interdum velit euismod in. Et tortor consequat id
          porta nibh venenatis cras sed. Adipiscing diam donec adipiscing
          tristique risus nec feugiat in fermentum. Non curabitur gravida arcu
          ac tortor dignissim convallis aenean et. Erat pellentesque adipiscing
          commodo elit. Rutrum tellus pellentesque eu tincidunt tortor aliquam
          nulla facilisi cras. Nunc id cursus metus aliquam eleifend. Justo nec
          ultrices dui sapien eget. Elementum pulvinar etiam non quam lacus
          suspendisse faucibus. Nibh mauris cursus mattis molestie a iaculis at.
          Urna nec tincidunt praesent semper feugiat. Est velit egestas dui id.
          Lobortis elementum nibh tellus molestie nunc non blandit. Tristique
          senectus et netus et malesuada fames ac. Sit amet risus nullam eget
          felis. Elementum pulvinar etiam non quam lacus suspendisse faucibus.
          Sit amet luctus venenatis lectus magna fringilla urna porttitor.
          Laoreet id donec ultrices tincidunt arcu non. Adipiscing elit duis
          tristique sollicitudin. Habitant morbi tristique senectus et. Turpis
          nunc eget lorem dolor. Accumsan lacus vel facilisis volutpat est velit
          egestas. Bibendum est ultricies integer quis auctor elit sed
          vulputate. Molestie at elementum eu facilisis sed odio morbi. Cursus
          turpis massa tincidunt dui ut ornare lectus sit. Egestas tellus rutrum
          tellus pellentesque eu tincidunt tortor. Adipiscing diam donec
          adipiscing tristique. At in tellus integer feugiat scelerisque varius
          morbi enim nunc. Risus pretium quam vulputate dignissim suspendisse.
          Amet nisl purus in mollis nunc. Non quam lacus suspendisse faucibus
          interdum posuere lorem. Urna cursus eget nunc scelerisque. In
          hendrerit gravida rutrum quisque. Adipiscing bibendum est ultricies
          integer quis auctor elit sed. Blandit turpis cursus in hac habitasse
          platea dictumst quisque. Diam vel quam elementum pulvinar etiam non
          quam. Scelerisque varius morbi enim nunc faucibus a pellentesque.
          Mauris cursus mattis molestie a iaculis at erat. Arcu ac tortor
          dignissim convallis aenean et tortor at.
        </Box>
        <Box
          sx={{
            gridColumn: 4,
            gridRow: 2,
            borderLeft: 1,
            borderColor: borderColor,
            display: "grid",
            gridTemplateRows: "1fr auto",
          }}
        >
          <Box sx={{ gridRow: 1 }}></Box>
          <Box sx={{ gridRow: 2 }}>
            <TextField
              sx={{ width: "100%", backgroundColor: "#ffffff" }}
              id="filled-textarea"
              label="Add a note"
              placeholder="Your note..."
              multiline
              variant="filled"
            />
          </Box>
        </Box>
      </Box>
    </ThemeProvider>
  );
}
