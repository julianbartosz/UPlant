import React, { useEffect } from 'react';
import useNotifications from '../../hooks/useNotifications';
import AddWithOptions from '../ui/AddWithOptions';
import { GenericButton } from '../buttons';


const NotificationForm = ({onBack, selectedGardenIndex}) => {

    const [selectedPlants, setSelectedPlants] = React.useState(new Set());

    const [newNotification, setNewNotification] = React.useState(null);

    const { mediateAddNotification } = useNotifications();

    const handlePlantSelection = (selected) => { 
        console.log("Selected plants:", selected);
        setSelectedPlants(new Set(selected));
    };

    const handleSubmit = () => {
        const nameInput = document.getElementById('name');
        const intervalInput = document.getElementById('interval');
        const name = nameInput?.value || '';

        const notification = {
            name: name,
            description: `Notification for ${name}`,
            interval: parseInt(intervalInput?.value, 10) || -1,
            plants: Array.from(selectedPlants).map((plant) => ({
                common_name: plant.common_name,
                id: plant.id,
            })),
        };

        console.log("Notification to be added:", notification);

        mediateAddNotification(selectedGardenIndex, notification);
    };

    return (
        <div style={{ fontFamily: 'Arial, sans-serif', fontSize: '14px', color: '#333', display: 'flex', justifyContent: 'center', alignItems: 'center'}}>
            <div style={{ width: '100%' }}>
                <div style={{ marginBottom: '20px' }}>
                    <GenericButton label="Cancel" onClick={onBack} style={{ backgroundColor: 'red', marginTop: '10px'}} />
                </div>
                <label
                    htmlFor="affected-plants"
                    style={{
                        marginBottom: '29px',
                        color: 'white',
                        fontFamily: 'cursive',
                    }}
                >
                    Affected Plants:
                </label>
                <AddWithOptions handleSelection={handlePlantSelection}/>
                <div style={{ marginTop: '15px',marginBottom: '10px', display: 'flex', flexDirection: 'column' }}>

                <label
                        htmlFor="name"
                        style={{
                            marginBottom: '5px',
                            color: 'white',
                            fontFamily: 'cursive',
                        }}
                    >
                        Name:
                    </label>
                    <div style={{ display: 'flex', flexDirection: 'column', width: '100%', alignItems: 'center' }}>
                        <input
                            type="text"
                            id="name"
                            name="name"
                            style={{
                                padding: '8px',
                                border: '1px solid #ccc',
                                borderRadius: '4px',
                                boxSizing: 'border-box',
                                width: '200px',
                                marginBottom: '15px',
                            }}
                        />
                    </div>
                    <label
                        htmlFor="interval"
                        style={{
                            marginBottom: '5px',
                            color: 'white',
                            fontFamily: 'cursive',
                        }}
                    >
                        Interval:
                    </label>
                    <div style={{ display: 'flex', flexDirection: 'column', width: '100%', alignItems: 'center' }}>
                        <input
                            type="number"
                            id="interval"
                            name="interval"
                            style={{
                                padding: '8px',
                                border: '1px solid #ccc',
                                borderRadius: '4px',
                                boxSizing: 'border-box',
                                width: '200px',
                                marginBottom: '15px'
                            }}
                        />
                    </div>
                </div>
                <GenericButton label="Submit" onClick={() => {handleSubmit();}} />
            </div>
        </div>
    );
};

export default NotificationForm;
