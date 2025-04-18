import React from 'react';
import { FaCog } from 'react-icons/fa';
import { BackButton } from '../buttons/index.js';
import { SiTacobell } from "react-icons/si";
import './styles/nav-bar.css';
import { useNavigate } from 'react-router-dom';

const NavBar = ({ username='Default', title = 'Default', buttonOptions = ['back', 'settings', 'bell' ], onBack=() => {} }) => {

    const navigate = useNavigate();
    return (
        <div className="navbar">
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
                {buttonOptions.includes('settings') && <FaCog className="settings-icon" onClick={() => {navigate('/settings')}} />}
                {buttonOptions.includes('bell') && <SiTacobell className="settings-icon" onClick={() => {navigate('/notifications')}} />}
</div>
            </div>
        </div>
    );
};

export default NavBar;
