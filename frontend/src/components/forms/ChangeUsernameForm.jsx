import React, { useState } from 'react';
import { GenericButton } from '../buttons';
import { useUser } from '../../hooks/useUser';
import './styles/change-username-form.css';

const ChangeUsernameForm = ({ onCancel }) => {
    const [username, setUsername] = useState('');

    const { mediateChangeUsername } = useUser();

    const handleSubmit = (e) => {
        e.preventDefault();
        mediateChangeUsername(username);
    };

    return (
        <div className="username-form">
            <div className="username-form-header">
                <GenericButton
                    label="Cancel"
                    onClick={onCancel}
                    style={{ backgroundColor: 'red' }}
                    className="username-form-cancel-button"
                />
            </div>

            <div className="username-form-input-container">
                <label htmlFor="username" className="username-form-label">
                    New Username:
                </label>
                <input
                    type="text"
                    id="username"
                    name="username"
                    className="username-form-input"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                />

                <div className="username-form-footer">
                    <GenericButton
                        className="username-form-button"
                        label="Submit"
                        onClick={handleSubmit}
                    />
                </div>
            </div>
        </div>
    );
};

export default ChangeUsernameForm;
