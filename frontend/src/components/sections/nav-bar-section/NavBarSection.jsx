// frontend/src/components/sections/nav-bar-section/NavBarSection.jsx

import React from 'react';
import { FaCog } from 'react-icons/fa';
import { BackButton } from '../../buttons/index.js';
import './styles/nav-bar-section.css'; // Adjust the path as necessary
import logo from '../../../assets/uplant_logo.png';


const NavBarSection = ({ username }) => {
    return (
        <div className="navbar">
            <BackButton />
            <h1>
            <img src={logo} alt="UPlant Logo" className="navbar-logo" />


            </h1>

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
