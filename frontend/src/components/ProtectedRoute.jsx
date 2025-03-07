import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext"; 

const ProtectedRoute = ({ children }) => {
  const { authToken } = useAuth();
  // If the user is not authenticated, redirect to login page
  // Skip to simulate successful login
  if (!authToken) {
    return <Navigate to="/login" />;
  }
  // If authenticated, render the children
  return children;
};

export default ProtectedRoute;