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
import { FidgetSpinner, TailSpin} from 'react-loader-spinner';

import './styles/data-table.css';



const DataTable = ({ 
        selectedGardenIndex,    
        onAdd,
        fontSize,
    }) => {
     
    const { mediateDeleteNotification, notificationsList} = useNotifications();
    
    // if (!notificationsList) {
    //     return (
    //         <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
    //             <FidgetSpinner  
    //                 visible={true}
    //                 height="80"
    //                 width="80"
    //                 ariaLabel="fidget-spinner-loading"
    //                 wrapperStyle={{}}
    //                 wrapperClass="fidget-spinner-wrapper"
    //                 ballColors={["#00BFFF", "#00BFFF", "#00BFFF"]}
    //                 backgroundColor="#F4442D"
    //             />
    //             <div style={{ marginLeft: '20px', fontSize: 'small' }}>Loading...</div>
    //         </div>
    //     );
    // }
    
    return (
        <>
            <table className="data-table" style={{ fontSize: fontSize }}>
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
                    {notificationsList && notificationsList[selectedGardenIndex] ? (
                    notificationsList[selectedGardenIndex].map((item, index) => (
                        item && (
                        <tr key={item.id}>
                            <td>{item.name}</td>
                            <td>
                                {item && item.plant_names && item.plant_names.map(plant_name => (
                                    <div key={item.id}>{plant_name}</div>
                                ))}
                            </td>
                            <td style={{ textAlign: 'center' }}>{item.interval}</td>
                            <td style={{ textAlign: 'center' }}>
                                <DeleteButton onClick={() => mediateDeleteNotification(selectedGardenIndex, index)} />
                            </td>
                        </tr>)
                    ))) : (

                            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                <FidgetSpinner  
                    visible={true}
                    height="80"
                    width="80"
                    ariaLabel="fidget-spinner-loading"
                    wrapperStyle={{}}
                    wrapperClass="fidget-spinner-wrapper"
                    ballColors={["#00BFFF", "#00BFFF", "#00BFFF"]}
                    backgroundColor="#F4442D"
                />
                <div style={{ marginLeft: '20px', fontSize: 'small' }}>Loading...</div>
            </div>
                 
                    )}
                </tbody>
            </table>
            {notificationsList && notificationsList[selectedGardenIndex] && notificationsList[selectedGardenIndex].length === 0  && (
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