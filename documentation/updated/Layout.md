# Layout Component

The `Layout` component provides the main structure for the application. It includes a sidebar with navigation links and a main content area where the other components are rendered.

## Props

| Prop | Type | Description |
| --- | --- | --- |
| `children` | `node` | The child components to be rendered in the main content area. |
| `isAuthenticated` | `bool` | A boolean value that indicates whether the user is authenticated. |

## Usage

```jsx
import React from 'react';
import { Link } from 'react-router-dom';

const Layout = ({ children, isAuthenticated }) => {
    if (!isAuthenticated) {
        return <>{children}</>;
    }

    return (
        <div className="flex h-screen bg-gray-800 text-white">
            <div className="w-64 bg-gray-900 p-4">
                <h4 className="my-3 text-xl font-bold">Trainer Portal</h4>
                <nav className="flex flex-col">
                    <Link to="/dashboard" className="py-2 px-4 rounded hover:bg-gray-700">Clients</Link>
                    <Link to="/exercise-library" className="py-2 px-4 rounded hover:bg-gray-700">Exercise Library</Link>
                    <Link to="/workout-dashboard" className="py-2 px-4 rounded hover:bg-gray-700">Workout Builder</Link>
                    <Link to="/prospect-management" className="py-2 px-4 rounded hover:bg-gray-700">Prospect Management</Link>
                    <Link to="/resource-hub" className="py-2 px-4 rounded hover:bg-gray-700">Resource Hub</Link>
                </nav>
            </div>
            <div className="flex-1 p-4 overflow-y-auto">
                {children}
            </div>
        </div>
    );
};

export default Layout;
```
