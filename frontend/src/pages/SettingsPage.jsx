import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChangePasswordForm, ChangeUsernameForm } from '../components/forms';
import { NavBar } from '../components/layout';
import { GenericButton } from '../components/buttons';
import './styles/settings-page.css';

const SettingsPage = ({ username = 'Default'}) => {
    const navigate = useNavigate();
    const [togglePasswordForm, setTogglePasswordForm] = useState(false);
    const [toggleUsernameForm, setToggleUsernameForm] = useState(false);
    
    const handleDeleteAccount = async () => {
        const endpoint = null;
        window.location.href = "https://www.google.com/";
        const requestBody = {
            username: username,
        };

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Token 4c1775be909a3873ee6c23104d433adaf4cbde29`,
                },
                body: JSON.stringify(requestBody),
            });

            if (!response.ok) {
                throw new Error('Failed to delete account');
            }

            alert('Account deleted successfully');
            navigate('/'); // Redirect to home or login page
        } catch (error) {
            window.location.href = "http://localhost:8000/api/users/logout/";

            console.error('Error deleting account:', error);
            alert('Error deleting account. Please try again later.');
        }

    }

    return (
        <div>
            <NavBar title="Settings" username={username} buttonOptions={['back']} onBack={() => navigate('/dashboard')} />
            <div className="settings-content">
                 {!togglePasswordForm && !toggleUsernameForm && (
            <div className="settings-form">
            <GenericButton
              label="Change Password"
              disableMouseOver={true}
              style={{ width: '66%' }}
              onClick={() => setTogglePasswordForm(true)}
            />
            <GenericButton
              label="Change Username"
              disableMouseOver={true}
              style={{ marginTop: '20px', width: '66%' }}
              onClick={() => setToggleUsernameForm(true)}
            />
            <GenericButton
              label="DELETE ACCOUNT"
              disableMouseOver={true}
              style={{ backgroundColor: 'red', marginTop: '20px', width: '66%' }}
              onClick={() => handleDeleteAccount()}
            />
          </div>
                )}
            {togglePasswordForm && <ChangePasswordForm onCancel={() => setTogglePasswordForm(false)} />}
            {toggleUsernameForm && <ChangeUsernameForm onCancel={() => setToggleUsernameForm(false)} />}
            </div>
        </div>
    );
};

export default SettingsPage;