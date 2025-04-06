// frontend/src/App.jsx

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import './App.css';
import GardenDashboard from './pages/GardenDashboard';
import ProtectedRoute from './contexts/ProtectedRoute.jsx';
import Catalog from './pages/Catalog'; 
import UserProvider from './contexts/ProtectedRoute';
import './styles/main.css';


function App() {
  
  return (
    <UserProvider>
    <DndProvider backend={HTML5Backend}>
      <Router basename='/app'>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          {/* Make sure you have a route for /dashboard */}
          <Route path="/dashboard" element={<GardenDashboard />} />
          <Route path="/About" element={<div>About Page Content</div>} />
          <Route path="/Catalog" element={<ProtectedRoute><Catalog/></ProtectedRoute>} />
          <Route path="/Signup" element={<div>Signup Page Content</div>} /> 
          <Route path="/Login" element={<div>Template Route Content</div>} />
          <Route path="/garden-dashboard" element={<ProtectedRoute><GardenDashboard/></ProtectedRoute>} />
          <Route path="*" element={<div>Page not found</div>} />
        </Routes>
      </Router>
    </DndProvider>
    </UserProvider>
  );
}

export default App;
