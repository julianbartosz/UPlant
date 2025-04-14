import React from 'react';
import { FaCog } from 'react-icons/fa';
import { BackButton } from '../../buttons/index.js';
import logoImage from '../../../assets/images/logo.png';
import './styles/nav-bar-section.css'; // Adjust the path as necessary

const NavBarSection = ({ username }) => {
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

export default NavBarSection;
