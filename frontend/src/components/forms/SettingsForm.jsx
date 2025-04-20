import { useState } from 'react';
import CryptoJS from 'crypto-js';
import { GenericButton } from '../buttons';
import { useUser } from '../../hooks/useUser';
import './styles/settings-form.css';

const SettingsForm = () => {

    const [password, setPassword] = useState('');
    const [username, setUsername] = useState('');
    const { updateUser, updatePassword, deleteAccount } = useUser();

    const handleUpdateUser = () => {
        updateUser(username);
    };

    const handleUpdatePassword = () => {
        updatePassword(password);
    };

    const handleDeleteAccount = () => {
        deleteAccount();
    };

    return (
        <div className="settings-form">
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