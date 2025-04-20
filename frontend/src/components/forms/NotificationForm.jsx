import { useState } from 'react';
import useNotifications from '../../hooks/useNotifications';
import AddWithOptions from '../ui/AddWithOptions';
import { GenericButton } from '../buttons';
import './styles/notification-form.css';

const NotificationForm = ({ setToggleForm, onBack, selectedGardenIndex, plantOptions }) => {
    const [selectedPlants, setSelectedPlants] = useState(new Set());

    const { mediateAddNotification } = useNotifications();

    const handlePlantSelection = (selected) => {
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

        setToggleForm(false);

        mediateAddNotification(selectedGardenIndex, notification);
    };

    return (
            <div className="notification-form-content">
                <div className="notification-form-header">
                    <GenericButton
                        label="Cancel"
                        onClick={onBack}
                        style={{backgroundColor: 'red'}}
                        className="notification-form-cancel-button"
                    />
                </div>

                <div className="notification-form-input-container">
                    <label htmlFor="name" className="notification-form-label">
                        Name:
                    </label>
                    <div className="notification-form-input-container">
                        <input
                            type="text"
                            id="name"
                            name="name"
                            className="notification-form-input"
                        />
                    </div>
                    <label htmlFor="interval" className="notification-form-label">
                        Interval:
                    </label>
                    <div className="notification-form-input-container">
                        <input
                            type="number"
                            id="interval"
                            name="interval"
                            className="notification-form-input"
                        />
                        <div className="notification-form-input-container">
                            <label
                                htmlFor="affected-plants"
                                className="notification-form-label"
                            >
                                Affected Plants:
                            </label>
                            <AddWithOptions
                                handleSelection={handlePlantSelection}
                                options={plantOptions}
                            />
                        </div>
                    </div>
                    <div className="notification-form-footer">
                    <GenericButton
                    className="notification-form-button"
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
