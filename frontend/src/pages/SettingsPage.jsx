import SettingsForm from '../components/forms/SettingsForm';
import { NavBar } from '../components/layout';

const SettingsPage = ({ username = 'Default'}) => {

    return (
        <div>
            <NavBar title="Settings" username={username} buttonOptions={['back']} onBack={() => { window.location.href = '/app/dashboard'; }} />
            <SettingsForm />
        </div>
    );

};

export default SettingsPage;