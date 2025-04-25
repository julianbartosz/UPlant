import { useState } from 'react';
import NotificationForm from '../forms/NotificationForm';
import DataTable from '../ui/DataTable';
import { useGardens } from '../../hooks/useGardens';
import './styles/notification-section.css';
import { useNotifications } from '../../hooks';

const NotificationSection = ({ contentSize, selectedGardenIndex }) => {
    const [toggleForm, setToggleForm] = useState(false);
    const { gardens } = useGardens();
    const plantOptions = [
        ...new Set(gardens[selectedGardenIndex]?.cells.flat().filter(item => item !== null))
      ];

    

    return (
        <div className='notification-section-container'>
            {toggleForm ? (
                    <NotificationForm setToggleForm={setToggleForm} plantOptions={plantOptions} onBack={() => setToggleForm(false)} selectedGardenIndex={selectedGardenIndex} />
                ) : (
                    <DataTable
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
