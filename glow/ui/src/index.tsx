import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import RunList from './runs/RunList';
import '@fontsource/roboto/300.css';
import '@fontsource/roboto/400.css';
import '@fontsource/roboto/500.css';
import '@fontsource/roboto/700.css';
import './index.css';
import { Route, BrowserRouter, Routes } from 'react-router-dom';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <BrowserRouter>
    <Routes>
      <Route path="/" element={<App />}>
        <Route path="runs" element={<RunList />} />
      </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
