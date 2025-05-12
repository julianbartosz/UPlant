/**
 * A dropdown component with multi-select functionality and customizable options.
 *
 * @component
 * @param {Object} props
 * @param {Function} [props.handleSelection=() => {}]
 * @param {Array<Object>} [props.options]
 * @param {string} [props.labelField="name"]
 * @param {string} [props.uniqueField="id"]
 * @returns {JSX.Element}
 */

import { useState } from 'react';
import Select from 'react-select';
import './styles/add-with-options.css';

const MAX_PLANTS_NOTIFICATION = 3;

const AddWithOptions = ({ 
    handleSelection=() => {},
    selectedOptions, 
    options=[],
    labelField="name", 
    uniqueField="id"
}) => {

const [error, setError] = useState(false);


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
                onChange={handleSelection}
                placeholder={ "" }
                getOptionLabel={(option) => option[labelField]}
                getOptionValue={(option) => option[uniqueField]}
            />
        </div>
    );
};

export default AddWithOptions;