/**
 * NotificationForm Component
 */

import { useState, useEffect } from 'react';
import { useNotifications } from '../../hooks';
import { AddWithOptions } from '../ui';
import { GenericButton } from '../buttons';
import './styles/form.css';

const NotificationForm = ({ 
    setToggleForm, onBack, selectedGardenIndex, plantOptions }) => {
    // Form state management
    const [selectedPlants, setSelectedPlants] = useState(new Set());
    const [formName, setFormName] = useState('');
    const [formType, setFormType] = useState(''); // No default type selected
    const [formInterval, setFormInterval] = useState(7); // Keep default interval at 7
    const [submitting, setSubmitting] = useState(false);
    const [errorMessage, setErrorMessage] = useState('');

    const { mediateAddNotification } = useNotifications();
  
    const handlePlantSelection = (selected) => {
        console.log("Plants selected:", selected);
        setSelectedPlants(new Set(selected));
    };

    const handleSubmit = () => {
        console.log("Submit button clicked");
        setErrorMessage('');
        setSubmitting(true);
        
        try {
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
                name: formName,
                type: formType,
                interval: formInterval,
                plants: Array.from(selectedPlants),
                gardenIndex: selectedGardenIndex
            });
            
            const plants = Array.from(selectedPlants).map(plant => ({
                common_name: plant.common_name,
                id: plant.id,
            }));
            
            console.log("Calling mediateAddNotification");
            mediateAddNotification(selectedGardenIndex, formName, formType, formInterval, plants, () => {
                console.log("Notification created successfully");
                setToggleForm(false);
            });
            
        } catch (error) {
            console.error("Error in form submission:", error);
            setErrorMessage(`Error: ${error.message || 'Unknown error occurred'}`);
        } finally {
            setSubmitting(false);
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