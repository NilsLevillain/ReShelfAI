import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import '@ds/tokens.css';
import '@ds/components.css';
import { App } from './App';
import { DataSourceProvider } from './data/DataSource';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <DataSourceProvider>
        <App />
      </DataSourceProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
