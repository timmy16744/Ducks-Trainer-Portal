# React Guide

React is a modern, component-based JavaScript library for building user interfaces. It emphasizes declarative programming, reusability, and a virtual DOM for efficient updates.

## Key Concepts

* **Components:** All UI is built from reusable, composable components. Use functional components and hooks for state and side effects.
* **JSX:** Write UI using JSX, a syntax extension that looks like HTML in JavaScript.
* **State & Props:** State is local to a component; props are used to pass data between components.
* **Hooks:** Use hooks like `useState`, `useEffect`, and `useContext` to manage state and side effects in functional components.
* **Suspense & Concurrent Features:** Modern React supports Suspense for data fetching and code splitting, and concurrent rendering for improved UX.

## Getting Started

The recommended way to start a React project is with Create React App or Vite:

```bash
npx create-react-app my-app
cd my-app
npm start
```

## Example: Functional Component with State

```jsx
import React, { useState } from 'react';
function Counter() {
  const [count, setCount] = useState(0);
  return (
    <button onClick={() => setCount(count + 1)}>
      Count: {count}
    </button>
  );
}
```

## Migration Notes (React 18/19+)
- Use `createRoot` instead of `ReactDOM.render`.
- Prefer functional components and hooks over class components.
- Use Suspense for async data and code splitting.

## Further Reading
- [React Official Documentation](https://react.dev/)
- [React Hooks](https://react.dev/reference/react)
- [React 19 Upgrade Guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide)