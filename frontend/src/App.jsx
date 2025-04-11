// frontend/src/App.jsx

import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import GardenDashboard from './pages/GardenDashboardPage.jsx';
import ProtectedRoute from './contexts/ProtectedRoute.jsx';
import Catalog from './pages/CatalogPage.jsx';
import UserProvider from './contexts/ProtectedRoute';
import './styles/app.css';

// Simple error boundary component to catch rendering errors
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error("React Error Boundary caught an error:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px', color: 'red' }}>
          <h2>Something went wrong</h2>
          <details style={{ whiteSpace: 'pre-wrap' }}>
            {this.state.error && this.state.error.toString()}
          </details>
          <button onClick={() => window.location.reload()}>
            Reload Page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  console.log("App component rendering");
  
  return (
    <ErrorBoundary>
      <UserProvider>
        <DndProvider backend={HTML5Backend}>
          <Router basename='/app'>
            <Routes>
              {/* Redirect root to dashboard */}
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              
              {/* Protected routes requiring authentication */}
              <Route path="/dashboard" element={
                <ProtectedRoute>
                  <GardenDashboard />
                </ProtectedRoute>
              } />
              
              <Route path="/catalog" element={
                <ProtectedRoute>
                  <Catalog />
                </ProtectedRoute>
              } />
              
              {/* Authentication routes */}
              <Route path="/login" element={
                // This redirects to the backend Django login page
                <Navigate to="/login/" replace />
              } />
              
              {/* 404 catch-all route */}
              <Route path="*" element={
                <div style={{ 
                  padding: '20px',
                  display: 'flex', 
                  flexDirection: 'column',
                  alignItems: 'center', 
                  justifyContent: 'center',
                  height: '100vh'
                }}>
                  <h1>Page Not Found</h1>
                  <p>The page you're looking for doesn't exist.</p>
                  <button onClick={() => window.location.href = '/app/dashboard'}>
                    Go to Dashboard
                  </button>
                </div>
              } />
            </Routes>
          </Router>
        </DndProvider>
      </UserProvider>
    </ErrorBoundary>
  );
}

export default App;