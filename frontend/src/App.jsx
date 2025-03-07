import { AuthProvider } from './context/AuthContext.jsx';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LoginPage from './pages/LoginPage.jsx';
import DashboardPage from './pages/DashboardPage.jsx';
import ProtectedRoute from './components/ProtectedRoute.jsx';
import './App.css'

function App() {
  return (
    <AuthProvider> 
      <Router>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          {/* ProtectedRoute ensures only authenticated users can access this route */}
          <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;