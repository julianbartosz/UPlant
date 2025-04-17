import React from 'react';
import { FaCog } from 'react-icons/fa';
import { BackButton } from '../buttons/index.js';
import './styles/nav-bar.css';

const NavBar = ({ username='Default', title = 'Default', buttonOptions = ['back', 'settings' ], onBack=() => {} }) => {
    return (
        <div className="navbar">
           
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
            </div>
        </div>
    );
};

export default NavBar;
