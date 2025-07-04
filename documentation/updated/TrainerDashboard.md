# TrainerDashboard Component

The `TrainerDashboard` component is the main view for the trainer. It displays a list of clients and provides access to other features such as group management, alerts, and program management.

## State

| State | Type | Description |
| --- | --- | --- |
| `clients` | `array` | A list of the trainer's clients. |
| `selectedClient` | `object` | The client that is currently selected. |
| `showModal` | `bool` | A boolean value that indicates whether the feature toggle modal is visible. |
| `showClientModal` | `bool` | A boolean value that indicates whether the client view modal is visible. |
| `clientToViewId` | `string` | The ID of the client to be viewed in the client view modal. |
| `activeTab` | `string` | The key of the currently active tab. |

## Functions

| Function | Description |
| --- | --- |
| `fetchClients` | Fetches the list of clients from the API. |
| `handleManageClick` | Sets the selected client and shows the feature toggle modal. |
| `handleViewClient` | Sets the client to be viewed and shows the client view modal. |
| `renderActiveTab` | Renders the content of the currently active tab. |

## Usage

```jsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import AddClientForm from './AddClientForm';
import FeatureToggleModal from './FeatureToggleModal';
import ClientViewModal from './ClientViewModal';
import GroupManagement from './GroupManagement';
import AlertsDashboard from './AlertsDashboard';
import ProgramManagement from './ProgramManagement';

const TrainerDashboard = () => {
    const [clients, setClients] = useState([]);
    const [selectedClient, setSelectedClient] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [showClientModal, setShowClientModal] = useState(false);
    const [clientToViewId, setClientToViewId] = useState(null);
    const [activeTab, setActiveTab] = useState('clients');

    const fetchClients = async () => {
        const response = await fetch('http://localhost:5000/api/clients', {
            headers: {
                'Authorization': 'Basic ' + btoa('trainer:password')
            }
        });
        const data = await response.json();
        setClients(data);
    };

    useEffect(() => {
        fetchClients();
    }, []);

    const handleManageClick = (client) => {
        setSelectedClient(client);
        setShowModal(true);
    };

    const handleViewClient = (clientId) => {
        setClientToViewId(clientId);
        setShowClientModal(true);
    };

    const renderActiveTab = () => {
        switch (activeTab) {
            case 'clients':
                return (
                    <div>
                        <AddClientForm fetchClients={fetchClients} />
                        <h2 className="text-2xl font-bold mb-4">Clients</h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {clients.map(client => (
                                <div key={client.id} className="bg-gray-700 rounded-lg p-4 flex justify-between items-center">
                                    <div>
                                        <button onClick={() => handleViewClient(client.id)} className="text-lg font-bold text-white hover:underline">{client.name} ({client.email})</button>
                                        <p className="text-gray-400">{client.unique_url}</p>
                                    </div>
                                    <div className="flex flex-col space-y-2">
                                        <button onClick={() => handleManageClick(client)} className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">Manage</button>
                                        <Link to={`/workout-dashboard`} className="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded text-center">Workout Builder</Link>
                                    </div>
                                </div>
                            ))}
                        </div>
                        {showModal && 
                            <FeatureToggleModal 
                                client={selectedClient} 
                                fetchClients={fetchClients} 
                                setShowModal={setShowModal} 
                            />
                        }
                        {showClientModal && clientToViewId && (
                            <ClientViewModal
                                clientId={clientToViewId}
                                show={showClientModal}
                                handleClose={() => setShowClientModal(false)}
                            />
                        )}
                    </div>
                );
            case 'groups':
                return <GroupManagement />;
            case 'alerts':
                return <AlertsDashboard />;
            case 'programs':
                return <ProgramManagement />;
            default:
                return null;
        }
    };

    return (
        <div>
            <div className="flex border-b border-gray-700">
                <button onClick={() => setActiveTab('clients')} className={`py-2 px-4 ${activeTab === 'clients' ? 'border-b-2 border-white' : ''}`}>Clients</button>
                <button onClick={() => setActiveTab('groups')} className={`py-2 px-4 ${activeTab === 'groups' ? 'border-b-2 border-white' : ''}`}>Group Management</button>
                <button onClick={() => setActiveTab('alerts')} className={`py-2 px-4 ${activeTab === 'alerts' ? 'border-b-2 border-white' : ''}`}>Alerts</button>
                <button onClick={() => setActiveTab('programs')} className={`py-2 px-4 ${activeTab === 'programs' ? 'border-b-2 border-white' : ''}`}>Program Management</button>
            </div>
            <div className="p-4">
                {renderActiveTab()}
            </div>
        </div>
    );
};

export default TrainerDashboard;
```
