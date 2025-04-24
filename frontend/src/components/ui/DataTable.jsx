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
import useNotifications from '../../hooks/useNotifications';
import { PiEmptyBold } from "react-icons/pi";

import './styles/data-table.css';

const DataTable = ({ 
        selectedGardenIndex,    
        onAdd,
        data=[],
        fontSize,
    }) => {
     
    const { mediateDeleteNotification} = useNotifications();


    return (
        <>
            <table className="data-table" style={{ fontSize: fontSize }}>
                <thead className="data-table-header">
                    <tr>
                        <th style={{ fontSize: 'small' }}>Name</th>
                        <th style={{ fontSize: 'small' }}>Plants</th>
                        <th style={{ fontSize: 'small' }}>Interval</th>
                        <th style={{ textAlign: 'center', fontSize: 'small' }}>
                            <AddButton onClick={onAdd} />
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {data.map((item, index) => (
                        <tr key={item.id}>
                            <td>{item.name}</td>
                            <td>
                                {item.plants.map((plant) => (
                                    <div key={plant.id}>{plant.common_name}</div>
                                ))}
                            </td>
                            <td style={{ textAlign: 'center' }}>{item.interval}</td>
                            <td style={{ textAlign: 'center' }}>
                                <DeleteButton onClick={() => mediateDeleteNotification(selectedGardenIndex, index)} />
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            {data.length === 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100% - 80px)', justifyContent: 'center', alignItems: 'center', fontSize: 'small' }}>
            <PiEmptyBold style={{height: "70px", width: "70px"}} />
            <ul>
                <li>You have zero configured notifications.</li>
                <li>Click the green "+" button to add a notification for your garden.</li>
            </ul>
            </div>)}
            </>
    );
};

export default DataTable;