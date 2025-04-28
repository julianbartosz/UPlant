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

import { useState } from 'react';
import { useNotifications }  from '../../hooks';
import { AddWithOptions } from '../ui';
import { GenericButton } from '../buttons';
import './styles/form.css';

const NotificationForm = ({ 
    setToggleForm, onBack, selectedGardenIndex, plantOptions }) => {
    const [selectedPlants, setSelectedPlants] = useState(new Set());

    const { mediateAddNotification } = useNotifications();
  
    const handlePlantSelection = (selected) => {
        setSelectedPlants(new Set(selected));
    };

    const handleSubmit = () => {
        const nameInput = document.getElementById('name');
        const intervalInput = document.getElementById('interval');
        const name = nameInput?.value || '';
        const plants = Array.from(selectedPlants).map((plant) => ({
            common_name: plant.common_name,
            id: plant.id,
        }));

        const interval = parseInt(intervalInput?.value, 10) || -1;

        mediateAddNotification(selectedGardenIndex, name, interval, plants, () => { 
            setToggleForm(false); 
        });
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
                        handleSubmit();
                    }}
                />
                </div>
                </div>
            </div>
    );
};

export default NotificationForm;
