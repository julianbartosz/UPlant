/**
 * @file AddWithOptions.jsx
 * @description A dropdown component with multi-select functionality and customizable options.
 * This component wraps the react-select library to provide a consistent interface for
 * multi-selection dropdowns throughout the application.
 * 
 * @component
 * @param {Object} props - Component props
 * @param {Function} [props.handleSelection=() => {}] - Callback function triggered when selection changes
 * @param {Array<Object>} [props.selectedOptions=[]] - Array of currently selected options
 * @param {Array<Object>} [props.options=[]] - Array of available options to choose from
 * @param {string} [props.labelField="name"] - Object field to use as display label
 * @param {string} [props.uniqueField="id"] - Object field to use as unique identifier
 * @returns {JSX.Element} - Rendered component
 * 
 * @details
 * - The component uses react-select for the dropdown implementation
 * - It filters out options that are already selected in the dropdown
 * - Custom styling for consistent appearance across the application
 * - Supports multi-selection with object arrays
 */
import Select from 'react-select';
import './styles/add-with-options.css';

const AddWithOptions = ({
    handleSelection = () => {},
    selectedOptions = [],
    options = [],
    labelField = "name",
    uniqueField = "id"
}) => {
    // Custom styles for the react-select component
    const customStyles = {
        option: (base) => ({
            ...base,
            color: 'black',
        }),
        placeholder: (base) => ({
            ...base,
            color: 'grey',
        }),
        container: (base) => ({
            ...base,
            width: '200px',
        }),
    };

    // Filter out options that are already selected
    const availableOptions = options.filter(
        option => !Array.from(selectedOptions).some(
            selected => selected[uniqueField] === option[uniqueField]
        )
    );

    return (
        <div className="add-with-options">
            <Select
                isMulti
                styles={customStyles}
                options={availableOptions}
                value={Array.from(selectedOptions)}
                onChange={handleSelection}
                placeholder=""
                getOptionLabel={(option) => option[labelField]}
                getOptionValue={(option) => option[uniqueField]}
            />
        </div>
    );
};

export default AddWithOptions;
