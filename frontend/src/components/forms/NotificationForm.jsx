/**
 * NotificationForm Component
 * 
 * @file NotificationForm.jsx
 * @component
 * @param {Object} props
 * @param {Function} props.setToggleForm - Callback to toggle the visibility of the form.
 * @param {Function} props.onBack - Callback to handle the cancel or back action.
 * @param {number} props.selectedGardenIndex - Index of the selected garden for the notification.
 * @param {Array} props.plantOptions - List of plant options to select from.
 * 
 * @returns {JSX.Element} The rendered NotificationForm component.
 * 
 * @example
 * <NotificationForm 
 *   setToggleForm={setToggleForm} 
 *   onBack={handleBack} 
 *   selectedGardenIndex={0} 
 *   plantOptions={plantOptions} 
 * />
 * 
 * @remarks
 * - The `interval` field must be a positive integer.
 * - The `plantOptions` should be an array of objects with `common_name` and `id` properties.
 * - Uses `mediateAddNotification` from the `useNotifications` hook logic to handle form submission.
 */

import { useContext, useState } from 'react';
import { useNotifications }  from '../../hooks';
import { AddWithOptions } from '../ui';
import { GenericButton } from '../buttons';
import './styles/form.css';
import useContentSize from '../../hooks/useContentSize';
import { UserContext } from '../../context/UserProvider';


const NotificationForm = ({ 
    setToggleForm, onBack, selectedGardenIndex, plantOptions }) => {
    const [selectedPlants, setSelectedPlants] = useState(new Set());

    const { gardens, dispatch } = useContext(UserContext);
    const handlePlantSelection = (selected) => {
        setSelectedPlants(new Set(selected));
    };

    const handleAddNotification = async () => {
        const gardenIndex = selectedGardenIndex;
        const nameInput = document.getElementById('name');
        const intervalInput = document.getElementById('interval');
        const name = nameInput?.value || '';
        const plants = Array.from(selectedPlants).map((plant) => ({
            common_name: plant.common_name,
            id: plant.id,
        }));
        const interval = parseInt(intervalInput?.value, 10) || -1;

        //   // Validation checks
        //   if (!plants || plants.length === 0) {
        //     alert('Please select at least one plant.');
        //     return;
        // }
    
        if (!name.trim()) {
            alert('Name cannot be empty.');
            return;
        }
    
        if (interval <= 0) {
            alert('Interval must be greater than 0.');
            return;
        }
    
        const isNameDuplicate = gardens[gardenIndex]['notifications']?.some(
            (existingNotification) => existingNotification.name.toLowerCase() === name.toLowerCase()
        );
    
        if (isNameDuplicate) {
            alert('Name must be unique.');
            return;
        }


        const rollback = { ...gardens[gardenIndex]['notifications'].filter(notification => notification.id === notificationId)[0] };

        const gardenId = gardens[gardenIndex].id;

        console.log("Garden ID:", gardenId);
    
        const newNotification = {
            garden: `${gardenId}`,
            name: name,
            type: "Other",
            interval: interval,
            next_due: new Date(Date.now() + interval * 24 * 60 * 60 * 1000).toISOString(),
            plant_names: plants.map((plant) => plant.common_name),
        };

    
    try {
        // Create notification
        const notificationResponse = await fetch('http://localhost:8000/api/notifications/notifications/', {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(newNotification),
        });

        if (!notificationResponse.ok) {
            console.error("Add notification failed", notificationResponse);
            return;
        } 

        const notificationData = await notificationResponse.json();
        console.log("Notification data:", notificationData);

        dispatch({ type: 'ADD_NOTIFICATION', garden_index: gardenIndex, payload: notificationData });

        // Process plants one at a time
        for (const plant of plants) {
            try {
                const plantResponse = await fetch(`http://localhost:8000/api/notifications/notifications/${notificationData.id}/add_plant/`, {
                    method: 'POST', // Changed to POST as GET with body is non-standard
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ plant_id: plant.id }), // Adjust based on API requirements
                });

                if (!plantResponse.ok) {
                    console.error("Add plant failed", plantResponse);
                    continue; // Continue with next plant
                }

                const plantData = await plantResponse.json();
                console.log("Plant association data:", plantData);
                dispatch({ type: 'ADD_PLANT', garden_index: gardenIndex, notification_id: notificationData.id, payload: plantData.common_name });
            } catch (error) {
                console.error("Error adding plant:", plant.id, error);
                // Continue with next plant instead of failing entirely
            }
        }

    } catch (error) {
        console.error("Error adding notification:", error);
    }
        };

    return (
            <div className="form-content">
                <div className="form-header">
                    <GenericButton
                        label="Cancel"
                        onClick={onBack}
                        style={{backgroundColor: 'red'}}
                        className="form-cancel-button"
                    />
                </div>
                <div className="form-input-container">
                    <label htmlFor="name" className="form-label">
                        Name:
                    </label>
                    <div className="form-input-container">
                        <input
                            type="text"
                            id="name"
                            name="name"
                            className="form-input"
                        />
                    </div>
                    <label htmlFor="interval" className="form-label">
                        Interval (in days):
                    </label>
                    <div className="form-input-container">
                        <input
                            type="number"
                            id="interval"
                            name="interval"
                            className="form-input"
                        />
                        <div className="form-input-container">
                            <label
                                htmlFor="affected-plants"
                                className="form-label"
                            >
                                Affected Plants:
                            </label>
                            <AddWithOptions
                                handleSelection={handlePlantSelection}
                                options={plantOptions}
                            />
                        </div>
                    </div>

                    <div className="form-footer">
                    <GenericButton
                    className="form-button"
                    label="Submit"
                    onClick={() => {
                        handleAddNotification();
                    }}
                />
                </div>
                </div>
            </div>
    );
};

export default NotificationForm;
