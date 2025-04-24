import React, { useState } from 'react';
import { GenericButton } from '../buttons';
import { useUser } from '../../hooks/useUser';
import './styles/change-password-form.css';

const ChangePasswordForm = ({ onCancel }) => {
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    const { mediateChangePassword } = useUser();

    const handleSubmit = (e) => {
        e.preventDefault();
        if (newPassword !== confirmPassword) {
            alert('New password and confirm password do not match.');
            return;
        }
        mediateChangePassword(currentPassword, newPassword, confirmPassword);
    };

    return (
        <div className="password-form">
            <div className="password-form-header">
                <GenericButton
                    label="Cancel"
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