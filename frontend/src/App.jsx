import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import './App.css';
import Login from './pages/Login.jsx';
import GardenDashboard from './pages/GardenDashboard.jsx';
import ProtectedRoute from './contexts/ProtectedRoute.jsx';

function App() {
  
  // TODO: Retrieve user info and authentication token from login redirect

  return (
    <DndProvider backend={HTML5Backend}>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/garden-dashboard" element={<ProtectedRoute><GardenDashboard/></ProtectedRoute>} />
        </Routes>
      </Router>
    </DndProvider>
  );
}

export default App;
