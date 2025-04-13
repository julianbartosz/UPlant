/**
 * 
 * @component
 * @param {Object} props
 * @param {Array} props.data
 *   @param {string} props.data[].id 
 *   @param {string} props.data[].name
 *   @param {Array} props.data[].plants
 *     @param {string} props.data[].plants[].id
 *     @param {string} props.data[].plants[].name 
 *   @param {string} props.data[].interval
 * @param {Function} props.setData 
 * @param {Object} [props.style={}] 
 * 
 */

import React from 'react';
import { DeleteButton, AddButton } from '../buttons';
import './styles/data-table.css';

const DataTable = ({ 
        data,
        setData,
        style,
    }) => {

    DataTable.defaultProps = {
        style: {},
    };
    
    const handleRemove = (idToRemove) => {
        setData((prev) => prev.filter((item) => item.id !== idToRemove));
    };

    return (
        <div className="container" style={style}>
            <table className="data-table">
                <thead className="data-table-header">
                    <tr>
                        <th style={{ fontSize: 'small' }}>Name</th>
                        <th style={{ fontSize: 'small' }}>Plants</th>
                        <th style={{ fontSize: 'small' }}>Interval</th>
                        <th style={{ textAlign: 'center', fontSize: 'small' }}>
                            <AddButton />
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {data.map((item) => (
                        <tr key={item.id}>
                            <td style={{ fontSize: 'medium' }}>{item.name}</td>
                            <td style={{ fontSize: 'small' }}>
                                {item.plants.map((plant) => (
                                    <div key={plant.id}>{plant.name}</div>
                                ))}
                            </td>
                            <td style={{ textAlign: 'center', fontSize: 'medium' }}>{item.interval}</td>
                            <td style={{ textAlign: 'center', fontSize: 'small' }}>
                                <DeleteButton onClick={() => handleRemove(item.id)} />
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default DataTable;