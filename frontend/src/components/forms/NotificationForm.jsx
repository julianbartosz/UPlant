/**
 * NotificationForm Component
 */

import { useState, useEffect, useContext } from 'react';
import { useNotifications } from '../../hooks';
import { AddWithOptions } from '../ui';
import { GenericButton } from '../buttons';
import { UserContext } from '../../context/UserProvider';
import './styles/form.css';
import { DEBUG } from '../../constants';

const NotificationForm = ({ 
    setToggleForm, 
    onBack, 
    selectedGardenIndex}) => {

    const [selectedPlants, setSelectedPlants] = useState(new Set());
    const [formName, setFormName] = useState('');
    const [formType, setFormType] = useState(''); 
    const [formInterval, setFormInterval] = useState(7);
    const [submitting, setSubmitting] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');
    const [plantOptions, setPlantOptions] = useState([]);  

    const { gardens, dispatch } = useContext(UserContext);

    useEffect(() => { 

        const determinePlantOptions = () => {
            if (DEBUG) console.log("--- Determining plant options ---");
            const garden = gardens[selectedGardenIndex];
            if (DEBUG) console.log('garden:', garden);
            const plant_options = garden.cells.flat().filter(cell => cell !== null).map(cell => ({ ...cell.plant_detail }));
            if (DEBUG) console.log("Plant options:", plant_options);
            const uniquePlants = Array.from(new Map(plant_options.map(plant => [plant.id, plant])).values());
            if (DEBUG) console.log("Unique plants:", uniquePlants);
            setPlantOptions(uniquePlants);
        };
        determinePlantOptions();
        
    }, [gardens, selectedGardenIndex]);

    const handlePlantSelection = (selected) => {
        console.log("Plants selected:", selected);
        setSelectedPlants(new Set(selected));
    };

    const handleSubmit = async () => {
        const gardenIndex = selectedGardenIndex;
        const type = formType;
        const interval = formInterval;
        const name = formName.trim();

        console.log("Submit button clicked");
        setErrorMessage('');
        setSubmitting(true);
        
        // Validation
        if (!formName.trim()) {
            setErrorMessage('Please enter a notification name');
            console.log("Validation failed: No name provided");
            setSubmitting(false);
            return;
        }
        
        if (!formType) {
            setErrorMessage('Please select a notification type');
            console.log("Validation failed: No type selected");
            setSubmitting(false);
            return;
        }
        
        if (formInterval < 1) {
            setErrorMessage('Interval must be at least 1 day');
            console.log("Validation failed: Invalid interval");
            setSubmitting(false);
            return;
        }
        
        if (selectedPlants.size === 0) {
            setErrorMessage('Please select at least one plant');
            console.log("Validation failed: No plants selected");
            setSubmitting(false);
            return;
        }

        console.log("Form validation passed, preparing submission");
        console.log({
            name: name,
            type: type,
            interval: interval,
            plants: Array.from(selectedPlants),
            gardenIndex: selectedGardenIndex,
            garden_id: gardens[gardenIndex].id
        });
        
        const plants = Array.from(selectedPlants).map(plant => ({
            name: plant.name,
            id: plant.id,
        }));
    
        const newNotification = {
            garden: `${gardens[gardenIndex].id}`,
            name: name,
            type: type,
            interval: 7,
            next_due: new Date(Date.now() + formInterval * 24 * 60 * 60 * 1000).toISOString(),
            plant_names: plants.map((plant) => plant.name),
        };

        console.log("New notification data:", newNotification);
    
        // Validation checks
        if (!plants || plants.length === 0) {
            alert('Please select at least one plant.');
            return;
        }
    
        if (!name.trim()) {
            alert('Name cannot be empty.');
            return;
        }
    
        if (formInterval <= 0) {
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
            
            // Process plants one at a time
            for (const plant of plants) {
                try {
                    const plantResponse = await fetch(`http://localhost:8000/api/notifications/notifications/${notificationData.id}/add_plant/`, {
                        method: 'POST', // Changed to POST as GET with body is non-standard
                        credentials: 'include',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ plant_id: plant.id }), 
                    });
    
                    if (!plantResponse.ok) {
                        console.error("Add plant failed", plantResponse);
                        continue; 
                    }
    
                    const plantData = await plantResponse.json();
                    console.log("Plant association data:", plantData);
                } catch (error) {
                    console.error("Error adding plant:", error);
                }
            }

            // Get the updated notification data
            const updatedNotificationResponse = await fetch(`http://localhost:8000/api/notifications/notifications/${notificationData.id}/`, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            if (!updatedNotificationResponse.ok) {
                console.error("Get updated notification failed", updatedNotificationResponse);
                return;
            }
            const updatedNotificationData = await updatedNotificationResponse.json();
            console.log("Updated notification data:", updatedNotificationData);
            dispatch({ type: 'ADD_NOTIFICATION', garden_index: selectedGardenIndex, payload: updatedNotificationData });
        } catch (error) {
            console.error("Error in form submission:", error);
            setErrorMessage(`Error: ${error.message || 'Unknown error occurred'}`);
        } finally {
            setSubmitting(false);
            setToggleForm(false);
        }
    }

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
            
            {errorMessage && (
                <div className="error-message" style={{color: 'red', margin: '10px 0'}}>
                    {errorMessage}
                </div>
            )}
            
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
                        value={formName}
                        onChange={(e) => setFormName(e.target.value)}
                        placeholder="Enter notification name"
                    />
                </div>

                <label htmlFor="type" className="form-label">
                    Notification Type:
                </label>
                <div className="form-input-container">
                    <select
                        id="type"
                        name="type"
                        className="form-input"
                        value={formType}
                        onChange={(e) => setFormType(e.target.value)}
                    >
                        <option value="">-- Select Type --</option>
                        <option value="WA">Water</option>
                        <option value="FE">Fertilize</option>
                        <option value="PR">Prune</option>
                        <option value="HA">Harvest</option>
                        <option value="OT">Other</option>
                        <option value="WE">Weather</option>
                    </select>
                </div>

                <label htmlFor="interval" className="form-label">
                    Interval (in days):
                </label>
                <div className="form-input-container">
                    <input
                        type="number"
                        id="interval"
                        name="interval"
                        min="1"
                        value={formInterval}
                        onChange={(e) => setFormInterval(parseInt(e.target.value) || 1)}
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
                        label={submitting ? "Submitting..." : "Submit"}
                        onClick={handleSubmit}
                        disabled={submitting}
                    />
                </div>
            </div>
        </div>
    );
};

export default NotificationForm;