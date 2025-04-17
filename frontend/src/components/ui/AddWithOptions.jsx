/**
 * A dropdown component with multi-select functionality and customizable options.
 *
 * @component
 * @param {Object} props
 * @param {Function} [props.handleSelection=() => {}]
 * @param {Array<Object>} [props.options]
 * @param {string} [props.labelField="common_name"]
 * @param {string} [props.uniqueField="id"]
 * 
 * @returns {JSX.Element}
 */

import React from 'react';
import Select from 'react-select';
import './styles/add-with-options.css';

const AddWithOptions = ({ 
    handleSelection=() => {},
    options=[], 
    labelField="common_name", 
    uniqueField="id"
}) => {
    
const [error, setError] = React.useState(false);
const [selectedOptions, setSelectedOptions] = React.useState(new Set());

const handleSelectChange = (selected) => {
    if (selected.length === 0) {
        setError(true);
    } else {
        setError(false);
    }
    setSelectedOptions(new Set(selected));
    handleSelection(selected);
};

    return (
        <div className={`add-with-options ${error ? 'shake' : ''}`}>
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
                    }),
                    container: (base) => ({
                        ...base,
                        width: '200px',
                    }),
                }}
                options={options.filter(option => !Array.from(selectedOptions).some(selected => selected[uniqueField] === option[uniqueField]))}
                value={Array.from(selectedOptions)}
                onChange={handleSelectChange}
                placeholder={ "" }
                getOptionLabel={(option) => option[labelField]}
                getOptionValue={(option) => option[uniqueField]}
            />
        </div>
    );
};



export default AddWithOptions;