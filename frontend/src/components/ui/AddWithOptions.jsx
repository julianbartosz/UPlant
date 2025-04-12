/**
 *
 * @component
 * @param {Object} props 
 * @param {Array<Object>} [props.options=[]] 
 * @param {Function} props.onAdd 
 * @param {string} [props.labelField]
 * @param {string} [props.uniqueField]
 */

import React from 'react';
import Select from 'react-select';
import { AddButton } from '../buttons';
import DataTable from './DataTable';
import './styles/add-with-options.css';

const AddWithOptions = ({ 
    onAdd,
    options=[{id: 0, common_name: "Plant1"}, {id: 1, common_name: "Plant2"}], 
    labelField="common_name", 
    uniqueField="id", 
}) => {
    
    const [selectedOptions, setSelectedOptions] = React.useState(new Set());
    const [error, setError] = React.useState(false);

    const handleSelectChange = (selected) => { 
        if (error) {
            setError(false);
        }
        setSelectedOptions(new Set(selected));
    };

    const handleAddClick = () => {
        if (selectedOptions.size === 0) {
            setError(true);
        } else {
            if (error) {
                setError(false);
            }
            onAdd(Array.from(selectedOptions));
        }
    };

    return (
        <div className={`add-with-options ${error ? 'shake' : ''}`}>
            <AddButton onClick={handleAddClick} />
            <Select
                isMulti
                styles={{
                    option: (base) => ({
                        ...base,
                        color: 'black',
                    }),
                    placeholder: (base) => ({
                        ...base,
                        color: error ? 'red' : 'grey',
                    })
                }}
                options={options.filter(option => !Array.from(selectedOptions).some(selected => selected[uniqueField] === option[uniqueField]))}
                value={Array.from(selectedOptions)}
                onChange={handleSelectChange}
                placeholder={ "Select options ..." }
                getOptionLabel={(option) => option[labelField]}
                getOptionValue={(option) => option[uniqueField]}
            />
      
        
      <DataTable />

        </div>
        
    );
};



export default AddWithOptions;