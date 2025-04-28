/**
 * ChangePasswordForm Component
 * 
 * @file ChangePasswordForm.jsx
 * @component
 * @param {Object} props
 * @param {Function} props.onCancel - Callback function to handle the cancel action.
 * 
 * @returns {JSX.Element} The rendered ChangePasswordForm component.
 * 
 * @example
 * <ChangePasswordForm onCancel={() => console.log('Cancel clicked')} />
 * 
 * @remarks
 * - The `newPassword` and `confirmPassword` must match.
 * - Success and error messages are automatically cleared after 5 seconds.
 * - Uses the `VITE_PASSWORD_CHANGE_API_URL` environment variable for the API endpoint.
 */

import { useEffect, useState } from 'react';
import { GenericButton } from '../buttons';
import { GridLoading } from '../widgets';
import './styles/form.css';

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
            setConfirmPassword('');
            setNewPassword('');
            setCurrentPassword('');
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
                    setMessage("success");
                    setConfirmPassword('');
                    setNewPassword('');
                    setCurrentPassword('');
                    console.log("Password changed successfully.");
                } else {
                    const errorData = await response.json();
                    console.log(errorData);
                    setError(errorData);
                    setConfirmPassword('');
                    setNewPassword('');
                    setCurrentPassword('');
                    console.error("Error changing password: ", errorData);
                }

            } catch (e) {
                setError(e.message);
                setConfirmPassword('');
                setNewPassword('');
                setCurrentPassword('');
                console.error("Error during password change: ", e);
            } finally {
                setLoading(false);
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
                <label htmlFor="currentPassword" className="form-label">
                    Current Password:
                </label>
                {error && error.current_password && Array.isArray(error.current_password) && error.current_password.map((err, index) => (
                    <div key={index} style={{ color: 'red' }}>{err.split('.')[0]}</div>
                ))}
                <input
                    type="password"
                    id="currentPassword"
                    name="currentPassword"
                    className="form-input"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                />
                <label htmlFor="newPassword" className="form-label">
                    New Password:
                </label>
                {error && error.new_password && Array.isArray(error.new_password) && error.new_password.map((err, index) => (
                    <div key={index} style={{ color: 'red' }}>{err.split('.')[0]}</div>
                ))}
                <input
                    type="password"
                    id="newPassword"
                    name="newPassword"
                    className="form-input"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                />

                <label htmlFor="confirmPassword" className="form-label">
                    Confirm Password:
                </label>
                
                <input
                    type="password"
                    id="confirmPassword"
                    name="confirmPassword"
                    className="form-input"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                />
                {error && !error.new_password && !error.current_password && <div style={{ color: 'red' }}>{error}</div>}
                {message && <div style={{ color: 'green' }}>{message}</div>}
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

export default ChangePasswordForm;