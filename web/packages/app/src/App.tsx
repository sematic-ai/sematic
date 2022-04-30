import { APP_TITLE } from '@glow-web/common';
import * as React from 'react';

export function App(): React.ReactElement {
  const [count, setCount] = React.useState(0);

  return (
    <div>
      <h1>Welcome on {APP_TITLE}!</h1>
      <p>
        This is the main page of our application where you can confirm that it
        is dynamic by clicking the button below.
      </p>

      <p>Current count: {count}</p>
      <button onClick={() => setCount((prev) => prev + 1)}>Increment</button>
    </div>
  );
}
