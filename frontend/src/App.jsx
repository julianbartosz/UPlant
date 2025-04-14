// frontend/src/App.jsx

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import GardenDashboard from './pages/GardenDashboardPage.jsx';
import ProtectedRoute from './contexts/ProtectedRoute.jsx';
import Catalog from './pages/CatalogPage.jsx'; 
import UserProvider from './contexts/ProtectedRoute';
import SettingsPage from './pages/SettingsPage.jsx';
import  AddWithOptions  from './components/ui/AddWithOptions.jsx';
import DataTable from './components/ui/DataTable.jsx';
import { useState } from 'react';
import './styles/app.css';


function App() {
  const [data, setData] = useState([{ id: 1, name: 'Alice', plants: [{ id: 101, name: 'Fern' }, { id: 102, name: 'Cactus' }], interval: 7 }, { id: 2, name: 'Bob', plants: [{ id: 103, name: 'Bamboo' }], interval: 14 }, { id: 3, name: 'Charlie', plants: [{ id: 104, name: 'Palm' }, { id: 105, name: 'Orchid' }], interval: 30 }]);
  const handleAdd = (newItem) => {
    console.log('New item added:', newItem);
  };
  
  return (
    <UserProvider>
    <DndProvider backend={HTML5Backend}>
      <Router basename='/app'>
        <Routes>
      
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<GardenDashboard />} />
          <Route path="/About" element={<div>About Page Content</div>} />
          <Route path="/catalog" element={<ProtectedRoute><Catalog/></ProtectedRoute>} />
          <Route path="/Signup" element={<div>Signup Page Content</div>} /> 
          <Route path="/Login" element={<div>Template Route Content</div>} />
          <Route path="/settings" element={<ProtectedRoute><SettingsPage/></ProtectedRoute>} />
          <Route path="/table" element={<ProtectedRoute><DataTable data={data} setData={setData} /></ProtectedRoute>} />
          <Route path="/add" element={<ProtectedRoute><AddWithOptions onAdd={handleAdd} /></ProtectedRoute>} />
          <Route path="*" element={<div>Page not found</div>} />
        </Routes>
      </Router>
    </DndProvider>
    </UserProvider>
  );
}

export default App;
