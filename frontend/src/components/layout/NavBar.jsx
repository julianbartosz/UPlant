import React from 'react';
import { FaCog } from 'react-icons/fa';
import { BackButton } from '../buttons/index.js';
import { SiTacobell } from "react-icons/si";
import { useNavigate } from 'react-router-dom';
import { useUser } from '../../hooks';
import './styles/nav-bar.css';

const NavBar = ({ 
    title = 'Default', 
    buttonOptions = ['back', 'settings', 'bell'], 
    onBack = () => {} 
}) => {

    const navigate = useNavigate();
    const { username } = useUser();

    return (
        <div className="navbar">
            <div className="left-container">
                {buttonOptions.includes('back') && <BackButton onClick={onBack} />}
            </div>
            <div className='title-container'>
                <h1>{title}</h1>
            </div>
            <div className="right-container">
                {username && (
                    <div className="username">
                        {username}
                    </div>
                )}
                {buttonOptions.includes('bell') && <SiTacobell className="right-option-icon" onClick={() => { navigate('/notifications'); }} />}
                {buttonOptions.includes('settings') && <FaCog className="right-option-icon" onClick={() => { navigate('/settings'); }} />}
            </div>
        </div>
    );
};

export default NavBar;
