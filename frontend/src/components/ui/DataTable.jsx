import React, { useState } from 'react';
import './styles/data-table.css';


const DataTable = () => {
    const initialData = [
        { id: 1, name: 'Alice', role: 'Engineer', status: 'Active' },
        { id: 2, name: 'Bob', role: 'Designer', status: 'Inactive' },
        { id: 3, name: 'Charlie', role: 'Manager', status: 'Active' },
      ];
  const [data, setData] = useState(initialData);

  const handleRemove = (idToRemove) => {
    setData((prev) => prev.filter(item => item.id !== idToRemove));
  };

return (
    <table className="data-table">
        <thead>
            <tr>
                <th>Name</th>
                <th>Role</th>
                <th>Status</th>
                <th></th>
            </tr>
        </thead>
        <tbody>
            {data.map(item => (
                <tr key={item.id}>
                    <td>{item.name}</td>
                    <td>{item.role}</td>
                    <td>{item.status}</td>
                    <td>
                        <button 
                            onClick={() => handleRemove(item.id)} 
                            title="Remove"
                        >
                            
                        </button>
                    </td>
                </tr>
            ))}
        </tbody>
    </table>
);
};

export default DataTable;