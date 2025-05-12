/**
 * @file NotificationSection.jsx
 * @version 1.0.0
 * @description This component renders a section for managing notifications, including a form for adding notifications
 * and a data table for displaying existing notifications.
 * 
 * @component
 * @param {Object} props - The props object.
 * @param {number} props.selectedGardenIndex
 * 
 * @example
 * <NotificationSection
 *   selectedGardenIndex={0}
 * />
 */
import { useState } from 'react';
import { NotificationForm } from '../forms';
import { DataTable } from '../ui';
import './styles/notification-section.css';

const NotificationSection = ({ selectedGardenIndex }) => {
    const [toggleForm, setToggleForm] = useState(false);

    return (
        <>
            {toggleForm ? (
                <div className="centered-content">
                    <NotificationForm
                        setToggleForm={setToggleForm}
                        onBack={() => setToggleForm(false)}
                        selectedGardenIndex={selectedGardenIndex}
                    />
                </div>
            ) : (
                <DataTable
                    selectedGardenIndex={selectedGardenIndex}
                    onAdd={() => setToggleForm(true)}
                />
            )}
        </>
    );
};

export default NotificationSection;
