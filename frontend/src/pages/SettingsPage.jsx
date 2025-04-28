import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChangePasswordForm, ChangeUsernameForm } from '../components/forms';
import { NavBar } from '../components/layout';
import { useUser } from '../hooks';
import { GenericButton } from '../components/buttons';
import './styles/settings-page.css';

const SettingsPage = () => {
  
    const navigate = useNavigate();
    const [togglePasswordForm, setTogglePasswordForm] = useState(false);
    const [toggleUsernameForm, setToggleUsernameForm] = useState(false);
    const { mediateDeleteAccount } = useUser();

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
              onClick={() => mediateDeleteAccount()}
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