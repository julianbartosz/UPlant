/**
 * ChangeUsernameForm Component
 * 
 * @file ChangeUsernameForm.jsx
 * @component
 * @param {Object} props
 * @param {Function} props.onCancel - Callback function to handle the cancel action.
 * 
 * @returns {JSX.Element} The rendered ChangeUsernameForm component.
 * 
 * @example
 * <ChangeUsernameForm onCancel={() => console.log('Cancel clicked')} />
 * 
 * @remarks
 * - The `newUsername` must be at least 5 characters long and different from the current username.
 * - Success and error messages are automatically cleared after 5 seconds.
 * - Uses the `VITE_USERNAME_CHANGE_API_URL` environment variable for the API endpoint.
 */

import { useEffect, useState } from 'react';
import { GenericButton } from '../buttons';
import { useUser } from '../../hooks/useUser';
import { GridLoading } from '../widgets';
import './styles/form.css';

const ChangeUsernameForm = ({ onCancel }) => {
    const [newUsername, setNewUsername] = useState(''); 
    const [message, setMessage] = useState(''); 
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const { username, setUsername } = useUser();

    useEffect(() => {
        const currentUsername = username; 
        if (currentUsername && currentUsername !== newUsername) {
            setNewUsername(currentUsername);
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

    const handleSubmit = () => {

        if (!newUsername) {
            alert('Username cannot be empty.');
            return;
        }
        if (newUsername === username) {
            alert('New username cannot be the same as the current username.');
            return;
        }
        if (newUsername.length < 5) {
            alert('Username must be at least 5 characters long.');
            return;
        }

        setLoading(true);

        (async () => {
            try {
                const url = import.meta.env.VITE_USERNAME_CHANGE_API_URL; 

                const requestBody = {
                    username: newUsername,
                };

                const response = await fetch(url, {
                    method: 'PATCH',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestBody),
                });

                if (response.ok) {
                    const result = await response.json();
                    setUsername(newUsername);
                    setMessage("Success");
                    console.log("Username updated successfully: ", result.username);
                } else {
                    const errorData = await response.json();
                    setNewUsername(username); // reset to previous username
                    setMessage("Error: " + response.statusText);
                    console.error("Error changing username:", errorData.message);
                }

            } catch (e) {
                setError("Error (severe): " + e.message);
                console.error("Error changing username: ", e);
            } finally {
                setLoading(false);
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
        <div className="form">
            <div className="form-header">
                <GenericButton
                    label="Return"
                    onClick={onCancel}
                    style={{ backgroundColor: 'red' }}
                    className="form-cancel-button"
                />
            </div>

            <div className="form-input-container">
                <label htmlFor="newUsername" className="form-label">
                    Change Username:
                </label>
                <input
                    type="text"
                    id="newUsername"
                    name="newUsername"
                    className="form-input"
                    value={newUsername}
                    onChange={(e) => setNewUsername(e.target.value)}
                />
               
               
                {message && <div style={{ color: 'green' }}>{message}</div>}
                {error && <div style={{ color: 'red' }}>{error}</div>}
                <div className="form-footer">
                    <GenericButton
                        className="form-button"
                        label="Submit"
                        onClick={handleSubmit}
                    />
                </div>
            </div>
        </div>
    );
};

export default ChangeUsernameForm;