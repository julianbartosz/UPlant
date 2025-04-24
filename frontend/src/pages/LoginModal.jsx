import React, { useState } from 'react';

function LoginModal() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isOpen, setIsOpen] = useState(false); // State to control popup visibility

  const handleSubmit = (e) => {
    e.preventDefault();
    console.log('Login attempted with:', { email, password });
    // Add your login logic here
    setIsOpen(false); // Close popup on successful submit (optional)
  };

  const openPopup = () => setIsOpen(true);
  const closePopup = () => setIsOpen(false);

  return (

    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      {/* Button to trigger the popup */}
      <button
        onClick={openPopup}
        className="bg-indigo-600 py-2 px-4 rounded-md hover:bg-indigo-700"
      >
        Open Login
      </button>

      {/* Popup Modal */}
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md relative">
            {/* Close Button */}
            <button
              onClick={closePopup}
              className="absolute top-2 right-2 text-black hover:text-gray-800"
            >
              ×
            </button>
            <h2 className="text-2xl font-bold mb-6 text-center text-black">Login</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="email" className="block text-sm font-medium">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-black"
                  placeholder="you@example.com"
                />
              </div>
              <div>
                <label htmlFor="password" className="block text-sm font-medium">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-black"
                  placeholder="••••••••"
                />
              </div>
              <button
                type="submit"
                className="w-full bg-indigo-600 py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                Sign In
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default LoginModal;