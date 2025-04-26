import React from 'react';
import { FaCog } from 'react-icons/fa';
import { BackButton } from '../../buttons/index.js';
<<<<<<< HEAD
import logoImage from '../../../assets/images/logo.png';
import './styles/nav-bar-section.css'; // Adjust the path as necessary
=======
import './styles/nav-bar-section.css';
>>>>>>> origin/Squibb5

const NavBarSection = ({ username='Default', title = 'Default', buttonOptions = ['back', 'settings' ], onBack=() => {} }) => {
    return (
        <div className="navbar">
<<<<<<< HEAD
           
                <BackButton />
            <div className="logo-container">
                <img 
                    src={logoImage} 
                    alt="UPlant Logo" 
                    className="nav-logo"
                />
            </div>

            <div style={{ display: 'flex', alignItems: 'center' }}>
                <div className="username-container">
                    {username}
                </div>
                <FaCog className="settings-icon" />
=======
            <div style = {{ width: '500px', height: '60px', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
                <div style={{marginLeft: '20px',display: 'flex', marginRight: 'auto'}}>
            {buttonOptions.includes('back') && <BackButton onClick={() => {onBack();}} />}
            </div>
            </div>
            <div style={{ textAlign: 'center', flex: 1, height: '60px', alignItems: 'center', display: 'flex', justifyContent: 'center' }}>
                <h1>{title}</h1>
            </div>
            <div style={{ display: 'flex', alignItems: 'center',  width: '500px' }}>
                <div style={{display: 'flex', marginLeft: 'auto'}}>
                {username && (
                    <div className="username-container">
                        {username}
                    </div>
                )}
                {buttonOptions.includes('settings') && <FaCog className="settings-icon" onClick={() => window.location.href = '/app/settings'} />}
</div>
>>>>>>> origin/Squibb5
            </div>
        </div>
    );
};

export default NavBarSection;
