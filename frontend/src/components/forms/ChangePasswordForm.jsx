import React, { useEffect, useState } from 'react';
import { GenericButton } from '../buttons';
import './styles/change-password-form.css';
import { GridLoading } from '../widgets';


const ChangePasswordForm = ({ onCancel }) => {
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [message, setMessage] = useState(''); 
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

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

        e.preventDefault();
        if (newPassword !== confirmPassword) {
            alert('New password and confirm password do not match.');
            return;
        }
            

        setLoading(true);

        (async () => {
            try {
                const endpoint = import.meta.env.VITE_PASSWORD_CHANGE_API_URL;

                const requestBody = {
                    current_password: currentPassword,
                    new_password: newPassword,
                    confirm_password: confirmPassword,
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
                    setConfirmPassword('');
                    setNewPassword('');
                    setCurrentPassword('');
                } else {
                    setConfirmPassword('');
                    setNewPassword('');
                    setCurrentPassword('');
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to change password');
                }
            } catch (e) {
                setLoading(false);
                setError(e.message);
                setConfirmPassword('');
                setNewPassword('');
                setCurrentPassword('');
            }

        })();
    };

    if (loading) {
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
                <label htmlFor="currentPassword" className="password-form-label">
                    Current Password:
                </label>
                <input
                    type="password"
                    id="currentPassword"
                    name="currentPassword"
                    className="password-form-input"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                />

                <label htmlFor="newPassword" className="password-form-label">
                    New Password:
                </label>
                <input
                    type="password"
                    id="newPassword"
                    name="newPassword"
                    className="password-form-input"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                />

                <label htmlFor="confirmPassword" className="password-form-label">
                    Confirm Password:
                </label>
                <input
                    type="password"
                    id="confirmPassword"
                    name="confirmPassword"
                    className="password-form-input"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
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

export default ChangePasswordForm;