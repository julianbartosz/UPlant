import { createContext, useState, useContext } from "react";

// Create AuthContext
const AuthContext = createContext();

// For credentials
export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [authToken, setAuthToken] = useState(localStorage.getItem("token") || null);

  // Login function (store token)
  const login = async (email, password) => {
    try {

      const response = await fetch("http://127.0.0.1:8000/api/token/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) throw new Error("Login failed");

      const data = await response.json();

     
      setAuthToken(data.access); // Save token in state
      localStorage.setItem("token", data.access); // Persist token
    } catch (error) {
      console.error(error);
    }
  };

  // Logout function (clear token)
  const logout = () => {
    setAuthToken(null);
    localStorage.removeItem("token");
  };

  return (
    <AuthContext.Provider value={{ authToken, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
