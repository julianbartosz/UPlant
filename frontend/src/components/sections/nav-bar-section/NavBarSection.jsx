import React from 'react';
import { FaCog } from 'react-icons/fa';
import { BackButton } from '../../buttons/index.js';
import './styles/nav-bar-section.css'; // Adjust the path as necessary

const NavBarSection = ({ username }) => {
    return (
        <div className="navbar">
           
                <BackButton />
            <h1>UPlant</h1>

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
