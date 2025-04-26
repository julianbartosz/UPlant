import React, { useEffect, useState } from 'react';
import { GenericButton } from '../buttons';
import { useUser } from '../../hooks/useUser';
import { GridLoading } from '../widgets';
import './styles/change-password-form.css';

const ChangeUsernameForm = ({ onCancel }) => {
    const [newUsername, setNewUsername] = useState(''); 
    const [message, setMessage] = useState(''); 
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const { username } = useUser();

    useEffect(() => {
        const storedUsername = username; 
        if (storedUsername) {
            setNewUsername(storedUsername);
        }
    }, [username]);

    useEffect(() => {
        if (message) {
            const timer = setTimeout(() => {
                setMessage('');
            }, 5000);
            return () => clearTimeout(timer);
        }
    }, [message]);

    useEffect(() => {
        if (error) {
            const timer = setTimeout(() => {
                setError(null);
            }, 5000);
            return () => clearTimeout(timer);
        }
    }, [error]);

    const handleSubmit = (e) => {
  
        setLoading(true);

        (async () => {
            try {
                const endpoint = 'http://localhost:8000/api/users/me/update_username/'; 

                const requestBody = {
                    username: newUsername,
                };

                const response = await fetch(endpoint, {
                    method: 'POST',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Token 4c1775be909a3873ee6c23104d433adaf4cbde29`,
                    },
                    body: JSON.stringify(requestBody),
                });

                if (response.ok) {
                    const result = await response.json();
                    setMessage(result.detail);
                    setLoading(false);
                    setNewUsername('');
                } else {
                    setNewUsername(username); // Reset to original username
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to change username');
                }
            } catch (e) {
                setLoading(false);
                setError(e.message);
                setNewUsername(username);
            }

        })();
    };

    if (loading || !username) {
        return (
            <div className="loading-container">
                <GridLoading />
            </div>
        );
    }

    return (
        <div className="password-form">
            <div className="password-form-header">
                <GenericButton
                    label="Return"
                    onClick={onCancel}
                    style={{ backgroundColor: 'red' }}
                    className="password-form-cancel-button"
                />
            </div>

            <div className="password-form-input-container">
                <label htmlFor="newUsername" className="password-form-label">
                    Change Username:
                </label>
                <input
                    type="text"
                    id="newUsername"
                    name="newUsername"
                    className="password-form-input"
                    value={newUsername}
                    onChange={(e) => setNewUsername(e.target.value)}
                />
               
               
                {message && <div style={{ color: 'green' }}>{message}</div>}
                {error && <div style={{ color: 'red' }}>{error}</div>}
                <div className="password-form-footer">
                    <GenericButton
                        className="password-form-button"
                        label="Submit"
                        onClick={handleSubmit}
                    />
                </div>
            </div>
        </div>
    );
};

export default ChangeUsernameForm;