


/**
 * SettingsForm Component
 * 
 * A React component that provides a settings form for updating user information, 
 * such as username and password, and deleting the user account. It includes 
 * input fields for username and password, along with buttons for updating 
 * these fields and deleting the account.
 * 
 * @component
 * @returns {JSX.Element} 
 */

import React, { useState } from 'react';
import CryptoJS from 'crypto-js';
import { GenericButton } from '../buttons';

const SettingsForm = () => {

    const [password, setPassword] = useState('');
    const [username, setUsername] = useState('');

    const handleUpdatePassword = (e) => {
        e.preventDefault();

        const confirmed = window.confirm("Are you sure you want to change your password?");

        if (!confirmed) {
            console.log("Password change cancelled");
            return;
        }

        if (password.length < 8) {
            console.error("Password must be at least 8 characters long");
            return;
        }

        // Hash the password before sending it
        const hashedPassword = CryptoJS.SHA256(password).toString();
        console.log("Password changed securely:", hashedPassword);

        // Send the hashed password to the server
    };

    const handleUpdateUser = (e) => {
        e.preventDefault();

        const confirmed = window.confirm("Are you sure you want to update your username?");
        if (!confirmed) {
            console.log("Username update cancelled");
            return;
        }
        console.log("Username updated to:", username);

    };

    const handleDeleteAccount = () => {
        const confirmed = window.confirm("Are you sure you want to delete your account? This action cannot be undone.");
        if (!confirmed) {
            console.log("Account deletion cancelled");
            return;
        }

        console.log("Account deleted");
        // Send a request to the server to delete the account
    };

    return (
        <div>
            <form>
                <div style={{ marginBottom: '1rem' }}>
                    <label htmlFor="username" style={{ marginRight: '0.5rem' }}>Username: </label>
                    <input 
                        type="text" 
                        id="username" 
                        name="username" 
                        style={{ marginRight: '0.5rem' }}
                        onChange={(e) => setUsername(e.target.value)}
                    />
                    <GenericButton 
                        onClick={handleUpdateUser} 
                    />
                </div>
            </form>
            <form>
                <div style={{ marginBottom: '1rem' }}>
                    <label htmlFor="password" style={{ marginRight: '0.5rem' }}>Password: </label>
                    <input 
                        type="password" 
                        id="password" 
                        name="password" 
                        style={{ marginRight: '0.5rem' }}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                    <GenericButton 
                        onClick={handleUpdatePassword} 
                    />
                </div>
            </form>
            <div style={{ marginTop: '5rem' }}>
                <button 
                    style={{ 
                        backgroundColor: 'red', 
                        color: 'white', 
                        padding: '1rem', 
                        border: 'none', 
                        borderRadius: '5px', 
                        cursor: 'pointer' 
                    }}
                    onClick={handleDeleteAccount}
                >
                    Delete Account
                </button>
            </div>
        </div>
    );
};

export default SettingsForm;