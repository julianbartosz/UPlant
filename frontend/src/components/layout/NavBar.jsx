/**
 * @file NavBar.jsx
 * @version 1.0.0
 * @description This component renders a navigation bar with customizable options such as a back button, 
 *              settings icon, and notification bell. It also displays the current user's username and 
 *              notification counts.
 * 
 * @component
 * @param {Object} props - The component props.
 * @param {string} [props.title='Default'] - The title displayed in the center of the navigation bar.
 * @param {Array<string>} [props.buttonOptions=['back', 'settings', 'bell']] - An array of strings specifying which buttons to display.
 * @param {Function} [props.onBack=() => {}] - A callback function triggered when the back button is clicked.
 * @returns {JSX.Element} - The JSX element for the navigation bar.
 * 
 * @details
 * - The `NavBar` component accepts the following props:
 *   - `title` (string): The title displayed in the center of the navigation bar. Defaults to 'Default'.
 *   - `buttonOptions` (array): An array of strings specifying which buttons to display. Options include 'back', 'settings', and 'bell'.
 *   - `onBack` (function): A callback function triggered when the back button is clicked.
 * 
 * - The `NotificationBell` subcomponent:
 *   - Displays a notification badge with the count of pending notifications.
 *   - The badge color changes to red if there are overdue notifications, otherwise green.
 *   - Clicking the bell navigates to the `/notifications` route.
 * 
 * - Behavior:
 *   - UserContext is only accessed when the 'bell' option is included in buttonOptions
 *   - If the bell option is included but user data is not available, the bell is not rendered
 *   - The username of the current user is displayed in the right container if available.
 * 
 * - Styling:
 *   - The component uses CSS from `./styles/nav-bar.css` for layout and design.
 *   - Inline styles are used for the notification badge positioning and appearance.
 * 
 * - Dependencies:
 *   - React hooks (`useContext`) for state management.
 *   - `react-icons` for icons (`FaCog`, `FaBell`).
 *   - `react-router-dom` for navigation (`useNavigate`).
 *   - `UserContext` for accessing the current user's information and notification counts (only when needed).
 */

import { useContext } from 'react';
import { FaCog } from 'react-icons/fa';
import { BackButton } from '../buttons/index.js';
import { FaBell } from "react-icons/fa";
import { useNavigate } from 'react-router-dom';
import { UserContext } from '../../context/UserProvider';
import './styles/nav-bar.css';

/**
 * Notification bell component that displays pending notifications
 * 
 * @component
 * @param {Object} props - The component props.
 * @param {number} props.totalPending - The total number of pending notifications.
 * @param {number} props.overdue - The number of overdue notifications.
 * @param {Function} props.onClick - A callback function triggered when the bell icon is clicked.
 * @returns {JSX.Element} - The JSX element for the notification bell.
 */
const NotificationBell = ({ totalPending, overdue, onClick }) => {
    return (
        <div className="notification-bell" onClick={onClick}>
            <div className="bell-icon" style={{ position: 'relative' }}>
                <FaBell className="right-option-icon" />
                {totalPending > 0 && (
                    <div
                        className="notification-badge"
                        style={{
                            backgroundColor: overdue > 0 ? '#ff4444' : 'white',
                            position: 'absolute',
                            top: '0px',
                            right: '0px',
                            borderRadius: '50%',
                            width: '18px',
                            height: '18px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: overdue > 0 ? 'white' : 'black',
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

/**
 * Navigation bar component
 */
const NavBar = ({ 
    title = 'Default', 
    buttonOptions = ['back', 'settings', 'bell'], 
    onBack = () => {}
}) => {
    const navigate = useNavigate();
    
    // Only access context if bell is in buttonOptions
    const showBell = buttonOptions.includes('bell');
    const contextData = showBell ? useContext(UserContext) : null;
    
    return (
        <div className="navbar">
            <div className="left-container">
                {buttonOptions.includes('back') && <BackButton onClick={onBack} />}
            </div>
            <div className="title-container">
                <h1>{title}</h1>
            </div>
            <div className="right-container">
                {/* Only render username if context data is available */}
                {contextData?.user && (
                    <div className="username">
                        {contextData.user.username || undefined}
                    </div>
                )}
                
                {/* Only render notification bell if context data is available */}
                {showBell && contextData?.user && contextData?.notificationsCounts && (
                    <NotificationBell
                        totalPending={contextData.notificationsCounts.total_pending}
                        overdue={contextData.notificationsCounts.overdue}
                        onClick={() => navigate('/notifications')}
                    />
                )}
                
                {buttonOptions.includes('settings') && (
                    <FaCog 
                        className="right-option-icon" 
                        onClick={() => navigate('/settings')} 
                    />
                )}
            </div>
        </div>
    );
};

export default NavBar;