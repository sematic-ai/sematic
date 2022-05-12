import React from 'react';
import AppBar from '@mui/material/AppBar';
import Typography from '@mui/material/Typography';
import LightModeIcon from '@mui/icons-material/LightMode';
import Toolbar from '@mui/material/Toolbar';
import Container from '@mui/material/Container';
import Button from '@mui/material/Button';
import Box from '@mui/system/Box';
import { Outlet } from 'react-router-dom';


const pages = [['Runs', '/runs'], ['Artifacts', '/'], ['Docs', '/']];


function App() {
  return (
  <>
    <AppBar>
    <Container maxWidth="xl">
      <Toolbar>
    <LightModeIcon />
        <Typography
              variant="h5"
              component="h1"
          sx={{
            marginRight: 2,
            marginLeft: 1,
          }}
        >
        Glow
        </Typography>
        <Box sx={{ flexGrow: 1, display: 'flex'}}>
          {pages.map((page) => (
            <Button
            key={page[0]}
              sx={{ marginY: 2, marginLeft: 7, color: 'white', display: 'block' }}
              href={page[1]}
          >
            {page[0]}
          </Button>
          ))}
        </Box>
    </Toolbar>
    </Container>
    </AppBar>
      <Container
        maxWidth="xl"
        sx={{ marginTop: 9,  paddingTop: 4}}
      >
        <Container maxWidth="xl">
          <Outlet />
          </Container>
    </Container>
  </>);
}

export default App;