import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChangePasswordForm, ChangeUsernameForm } from '../components/forms';
import { NavBar } from '../components/layout';

import { GenericButton } from '../components/buttons';
import { useUser } from '../hooks/useUser';
import './styles/settings-page.css';



const SettingsPage = ({ username = 'Default'}) => {
    const navigate = useNavigate();
    const [togglePasswordForm, setTogglePasswordForm] = useState(false);
    const [toggleUsernameForm, setToggleUsernameForm] = useState(false);

    useEffect(() => {
        console.log(togglePasswordForm);
        console.log(toggleUsernameForm);
    }, [togglePasswordForm, toggleUsernameForm]);
    return (
        <div>
            <NavBar title="Settings" username={username} buttonOptions={['back']} onBack={() => navigate('/app/dashboard')} />
                {!togglePasswordForm && !toggleUsernameForm && (
            <div className="settings-form">
                <GenericButton onClick={() => setTogglePasswordForm(true)}>Change Password</GenericButton>
                <GenericButton onClick={() => setToggleUsernameForm(true)}>Change Username</GenericButton>
                </div>
                )}
            {togglePasswordForm && <ChangePasswordForm onCancel={() => setTogglePasswordForm(false)} />}
            {toggleUsernameForm && <ChangeUsernameForm onCancel={() => setToggleUsernameForm(false)} />}
                
            
        </div>
    );
};

export default SettingsPage;