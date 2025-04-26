import React, { useState } from 'react';

function SignupPage() {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isOpen, setIsOpen] = useState(false); // State for popup visibility

    const handleSubmit = (e) => {
        e.preventDefault();
        console.log('Signup attempted with:', { username, email, password });
        // Add your signup logic here (e.g., API call)
        setIsOpen(false); // Close popup on successful submit (optional)
    };

    const openPopup = () => setIsOpen(true);
    const closePopup = () => setIsOpen(false);

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100">
            {/* Button to trigger the popup */}
            <button
                onClick={openPopup}
                className="bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700"
            >
                Open Signup
            </button>

            {/* Popup Modal */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
                    onClick={closePopup} // Close when clicking overlay
                >
                    <div
                        className="bg-white p-8 rounded-lg shadow-md w-full max-w-md relative"
                        onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside
                    >
                        {/* Close Button */}
                        <button
                            onClick={closePopup}
                            className="absolute top-2 right-2 text-black hover:text-gray-800"
                        >
                            ×
                        </button>
                        <h2 className="text-2xl font-bold mb-6 text-center text-black">Sign Up</h2>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label htmlFor="username" className="block text-sm font-medium text-black">
                                    Username
                                </label>
                                <input
                                    id="username"
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    required
                                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-black"
                                    placeholder="Your username"
                                />
                            </div>
                            <div>
                                <label htmlFor="email" className="block text-sm font-medium text-black">
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
                                <label htmlFor="password" className="block text-sm font-medium text-black">
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
                                className="w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                            >
                                Sign Up
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

export default SignupPage;