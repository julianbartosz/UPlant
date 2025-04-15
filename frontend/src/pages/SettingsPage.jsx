import SettingsForm from '../components/forms/SettingsForm';
import NavBarSection from '../components/sections/nav-bar-section/NavBarSection';

const SettingsPage = ({ username = 'Default'}) => {

    return (
        <div>
            <NavBarSection title="Settings" username={username} buttonOptions={['back']} />
            <SettingsForm />
        </div>
    );

};

export default SettingsPage;