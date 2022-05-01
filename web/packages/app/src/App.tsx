import { APP_TITLE } from '@glow-web/common';
import * as React from 'react';
import Dashboard from './Dashboard';

export function App(): React.ReactElement {
  const [count, setCount] = React.useState(0);

  return (
    <div>
      <Dashboard />
    </div>
  );
}
