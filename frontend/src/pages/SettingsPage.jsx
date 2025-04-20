import { SettingsForm } from '../components/forms';
import { NavBar } from '../components/layout';
import { useNavigate } from 'react-router-dom';

const SettingsPage = ({ username = 'Default'}) => {
    const navigate = useNavigate();

    return (
        <div>
            <NavBar title="Settings" username={username} buttonOptions={['back']} onBack={() => navigate('/app/dashboard')} />
            <SettingsForm />
        </div>
    );
};

export default SettingsPage;