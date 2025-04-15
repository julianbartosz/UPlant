import React, { useEffect, useState } from 'react';
import ToggleSwitch from '../../ui/ToggleSwitch';
import NotificationForm from '../../forms/NotificationForm';
import DataTable from '../../ui/DataTable';
import Legend from '../../ui/Legend';
import { use } from 'react';

const NotificationsSection = ({ notifications, selectedGardenIndex }) => {

    if (!notifications) {
        return <div>Loading Notifications ...</div>;
    }

    const [toggleForm, setToggleForm] = useState(false);
    const [toggleLegend, setToggleLegend] = useState(false);

    const handleToggleLegend = () => {
        setToggleLegend(!toggleLegend);
    };

    const handleToggleForm = () => {
        setToggleForm(!toggleForm);
    };

    useEffect(() => {
        if (toggleLegend && toggleForm) {
            setToggleForm(false);
        }
    }, [toggleLegend]);

    return (
        <div className='notifications-section'>
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <ToggleSwitch
                id="toggle-notification-form"
                label="Add Notification"
                initialChecked={toggleForm}
                onToggle={handleToggleLegend}
                style={{ marginBottom: '20px' }}
            />
            </div>
            <div>
            {!toggleLegend && (
              
                toggleForm ? (
                    <NotificationForm onBack={() => setToggleForm(false)} />
                ) : (
                    
                    <DataTable
                        data={notifications[selectedGardenIndex]}
                        onAdd={() => setToggleForm(true)}
                        setData={() => {}}
                    />
                )
            )}
            </div>
            {toggleLegend && (
                <Legend
                    items={notifications[selectedGardenIndex].map(notification => ({
                        name: notification.name,
                        color: `#${Math.floor(Math.random() * 16777215).toString(16)}`
                    }))}
                />
            )}
        </div>
    );
};

export default NotificationsSection;
