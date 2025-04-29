import { useContext, useState } from 'react';
import NotificationForm from '../forms/NotificationForm';
import DataTable from '../ui/DataTable';
import { UserContext } from '../../context/UserProvider';
import './styles/notification-section.css';

const NotificationSection = ({ contentSize, selectedGardenIndex }) => {
    const [toggleForm, setToggleForm] = useState(false);
    const { gardens } = useContext(UserContext)
    const plantOptions = gardens[selectedGardenIndex]?.cells
        .flat()
        .filter(item => item !== null)
        .reduce((unique, item) => {
            if (!unique.some(plant => plant.id === item.id)) {
                unique.push(item);
            }
            return unique;
        }, []);

    return (
        <div className='notification-section-container'>
            {toggleForm ? (
                    <NotificationForm setToggleForm={setToggleForm} plantOptions={plantOptions} onBack={() => setToggleForm(false)} selectedGardenIndex={selectedGardenIndex} />
                ) : (
                    <DataTable
                        selectedGardenIndex={selectedGardenIndex}
                        onAdd={() => setToggleForm(true)}
                        setData={() => {}}
                        fontSize={contentSize.width / 50}
                    />
                )}
        </div>
    );
};

export default NotificationSection;
