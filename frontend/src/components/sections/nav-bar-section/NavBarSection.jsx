import React from 'react';
import { FaCog } from 'react-icons/fa';
import { BackButton } from '../../buttons/index.js';
import './styles/nav-bar-section.css';

const NavBarSection = ({ username='Default', title = 'Default', buttonOptions = ['back', 'settings' ] }) => {
    return (
        <div className="navbar">
            <div style = {{ width: '200px' }}>
            {buttonOptions.includes('back') && <BackButton />}
            </div>
            <div style={{ textAlign: 'center', flex: 1 }}>
                <h1>{title}</h1>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '200px' }}>
                {username && (
                    <div className="username-container">
                        {username}
                    </div>
                )}
                {buttonOptions.includes('settings') && <FaCog className="settings-icon" />}

            </div>
        </div>
    );
};

export default NavBarSection;
