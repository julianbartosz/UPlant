import React, { useEffect, useState } from 'react';
import ToggleSwitch from '../ui/ToggleSwitch';
import NotificationForm from '../forms/NotificationForm';
import DataTable from '../ui/DataTable';
import Legend from '../ui/Legend';

const NotificationSection = ({ plantOptions, contentSize, notifications, selectedGardenIndex }) => {

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
        <div style={{width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', alignSelf: 'end'}}>
            {/* <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center'}}>
            <ToggleSwitch
                id="toggle-notification-form"
                label="Add Notification"
                initialChecked={toggleForm}
                onToggle={handleToggleLegend}
                style={{ marginBottom: '20px' }}
            />
            </div> */}
            {!toggleLegend && (
              
                toggleForm ? (
                    <NotificationForm setToggleForm={setToggleForm}plantOptions={plantOptions} onBack={() => setToggleForm(false)} selectedGardenIndex={selectedGardenIndex} />
                ) : (
                    
                    <DataTable
                        data={notifications[selectedGardenIndex]}
                        selectedGardenIndex={selectedGardenIndex}
                        onAdd={() => setToggleForm(true)}
                        setData={() => {}}
                        fontSize={contentSize / 50}
                    />
                )
            )}
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

export default NotificationSection;
