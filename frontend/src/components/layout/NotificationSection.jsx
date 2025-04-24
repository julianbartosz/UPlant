import { useState } from 'react';
import NotificationForm from '../forms/NotificationForm';
import DataTable from '../ui/DataTable';
import './styles/notification-section.css';

const NotificationSection = ({ plantOptions, contentSize, notificationsList, selectedGardenIndex }) => {
    const [toggleForm, setToggleForm] = useState(false);

    return (
        <div className='notification-section-container'>
            {toggleForm ? (
                    <NotificationForm setToggleForm={setToggleForm}plantOptions={plantOptions} onBack={() => setToggleForm(false)} selectedGardenIndex={selectedGardenIndex} />
                ) : (
                    <DataTable
                        data={notificationsList[selectedGardenIndex]}
                        selectedGardenIndex={selectedGardenIndex}
                        onAdd={() => setToggleForm(true)}
                        setData={() => {}}
                        fontSize={contentSize / 50}
                    />
                )}
        </div>
    );
};

export default NotificationSection;
