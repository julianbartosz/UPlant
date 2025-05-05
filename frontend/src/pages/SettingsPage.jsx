import { useContext, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChangePasswordForm, ChangeUsernameForm } from '../components/forms';
import { NavBar } from '../components/layout';
import { GenericButton } from '../components/buttons';
import { UserContext } from '../context/UserProvider';
import { BASE_API, LOGIN_URL, DEBUG } from '../constants';
import './styles/settings-page.css';

const SettingsPage = () => {
  
    const navigate = useNavigate();
    const [togglePasswordForm, setTogglePasswordForm] = useState(false);
    const [toggleUsernameForm, setToggleUsernameForm] = useState(false);
    
    const handleDeleteAccount = async () => {
        
        const response = await fetch(`${BASE_API}/users/me/delete/`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ password: prompt("Please enter your password to confirm account deletion:") })
        });
        if (response.ok) {
            console.log("Account deleted successfully");
            window.location.href = LOGIN_URL;
        } else {
            console.error('Error deleting account:', response.statusText);
        }
    }

    return (
        <div>
            <NavBar title="Settings" buttonOptions={['back']} onBack={() => navigate('/dashboard')} />
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