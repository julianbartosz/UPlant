import React from 'react';
import { FaCog } from 'react-icons/fa';
import { BackButton } from '../buttons/index.js';
import { FaBell } from "react-icons/fa";
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
    const [notificationCounts, setNotificationCounts] = React.useState({ total_pending: 0, overdue: 0 });

    React.useEffect(() => {
        const fetchCounts = async () => {
            try {
                const response = await fetch('http://localhost:8000/api/notifications/instances/counts/', {
                    credentials: 'include'
                });
                const data = await response.json();
                setNotificationCounts(data);
            } catch (error) {
                console.error('Error fetching notification counts:', error);
            }
        };
        fetchCounts();
    }, []);

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
                {buttonOptions.includes('bell') && (
                    <NotificationBell
                        totalPending={notificationCounts.total_pending}
                        overdue={notificationCounts.overdue}
                        onClick={() => navigate('/notifications')}
                    />
                )}
                {buttonOptions.includes('settings') && <FaCog className="right-option-icon" onClick={() => { navigate('/settings'); }} />}
            </div>
        </div>
    );
};

    export default NavBar;

    const NotificationBell = ({ totalPending, overdue, onClick }) => {
        return (
            <div className="notification-bell" onClick={onClick}>
                <div className="bell-icon" style={{ position: 'relative' }}>
                    <FaBell className="right-option-icon"/>
                    {totalPending > 0 && (
                        <div
                            className="notification-badge"
                            style={{
                                backgroundColor: overdue > 0 ? '#ff4444' : '#44b700',
                                position: 'absolute',
                                top: '0px', // Adjust to position in the corner
                                right: '0px', // Adjust to position in the corner
                                borderRadius: '50%',
                                width: '18px',
                                height: '18px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                color: 'white',
                                fontSize: '12px',
                                fontWeight: 'bold',
                                marginRight: 'auto',
                                outline: 'black solid 2px'
                            }}
                        >
                            {totalPending}
                        </div>
                    )}
                </div>
            </div>
        );
    };
