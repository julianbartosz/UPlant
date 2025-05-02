/**
 * This component renders a table displaying a list of notificationsList, their associated plants, and time intervals.
 * It allows adding new entries and removing existing ones.
 * 
 * @component
 * @param {Object} props
 * @param {Array} props.data
 *   @param {string} props.data[].id
 *   @param {string} props.data[].name
 *   @param {Array} props.data[].plants
 *     @param {string} props.data[].plants[].id
 *     @param {string} props.data[].plants[].common_name
 *   @param {string} props.data[].interval 
 * @param {Function} props.setData 
 * @param {Object} [props.style={}]
 * @param {Function} props.onAdd 
 * @returns {JSX.Element}
 */

import { DeleteButton, AddButton } from '../buttons';
import { PiEmptyBold } from "react-icons/pi";
import { FidgetSpinner } from 'react-loader-spinner';
import { UserContext } from '../../context/UserProvider';

import './styles/data-table.css';
import { useContext } from 'react';

const DataTable = ({ 
        selectedGardenIndex,    
        onAdd,
    }) => {

    const {gardens, dispatch, loading} = useContext(UserContext);

    if (loading) return null;

    const handleDeleteNotification = (gardenIndex, notificationId) => {

        if (!window.confirm("Are you sure you want to delete this notification?")) {
            return;
        }
        
        const notificationUrl = `${import.meta.env.VITE_NOTIFICATIONS_API_URL}${notificationId}/`
        console.log(`Deleting notification at ${notificationUrl}`);

        (async () => {
            try {
                const response = await fetch(notificationUrl, {
                    method: 'DELETE',
                    credentials: 'include',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                });
                if (!response.ok) {
                    alert("Failed to delete notification. Please try again.");
                    return;
                } else {
                    console.log(`Notification deleted successfully:`);
                    dispatch({ type: 'REMOVE_NOTIFICATION', garden_index: gardenIndex, notification_id: notificationId });
                }
            } catch (error) {
                console.error("Error deleting notification:", error);
                alert(error.message);
            }
        })();
    }   


 
    return (
        <>
            <table className="data-table" >
                <thead className="data-table-header">
                    <tr>
                        <th style={{ textAlign: 'center', fontSize: 'small' }}>Name</th>
                        <th style={{ textAlign: 'center',fontSize: 'small' }}>Plants</th>
                        <th style={{ textAlign: 'center', fontSize: 'small' }}>Interval</th>
                        <th style={{ textAlign: 'center', fontSize: 'small' }}>
                            <AddButton onClick={onAdd} />
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {gardens[selectedGardenIndex]['notifications'] && (
                    gardens[selectedGardenIndex]['notifications'].map((item, _) => (
                        item && (
                        <tr key={item.id}>
                            <td>{item.name}</td>
                            <td>
                                {item && item.plant_names && item.plant_names.map(plantName => (
                                    <div key={plantName}>{plantName}</div>
                                ))}
                            </td>
                            <td style={{ textAlign: 'center' }}>{item.interval}</td>
                            <td style={{ textAlign: 'center' }}>
                                <DeleteButton onClick={() => handleDeleteNotification(selectedGardenIndex, item.id)} />
                            </td>
                        </tr>)
                    )))}
                </tbody>
            </table>
            {gardens && gardens[selectedGardenIndex] && gardens[selectedGardenIndex]['notifications'].length === 0  && (
            <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100% - 80px)', justifyContent: 'center', alignItems: 'center', fontSize: 'small' }}>
            <PiEmptyBold style={{color: 'black', height: "70px", width: "70px"}} />
            <ul>
                <li style={{color: 'black'}}>You have zero configured notifications.</li>
                <li style={{color: 'black'}}>Click the green "+" button to add a notification for your garden.</li>
            </ul>
            </div>)}
            </>
    );
};

export default DataTable;