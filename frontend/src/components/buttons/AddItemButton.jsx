/**
 * AddItemButton Component
 * 
 * @file AddItemButton.jsx
 * @component
 * @param {Object} props
 * @param {Function} props.onClick - Callback function to trigger when the button is clicked.
 * @param {string} props.ariaLabel - ARIA label for accessibility.
 * @param {string} [props.className] - Additional CSS class for styling.
 * @returns {JSX.Element} The rendered AddItemButton component.
 * 
 * @example
 * <AddItemButton
 *   onClick={() => console.log('Add item')}
 *   ariaLabel="Add new recurring reminder"
 * />
 * 
 * @remarks
 * - Displays a styled button with a plus icon and label for adding items.
 * - Uses a gradient background and hover effect for visual appeal.
 * - Styled with `add-item-button.css`.
 * - Requires `react-icons/fi` for the FiPlus icon.
 */
import { FiPlus } from 'react-icons/fi';
import './styles/add-item-button.css';

const AddItemButton = ({ onClick, ariaLabel, className = '' }) => {
  return (
    <button
      className={`add-item-button ${className}`}
      onClick={onClick}
      aria-label={ariaLabel}
    >
      <FiPlus className="add-item-icon" />
      <span className="add-item-label">Add a new recurring reminder</span>
    </button>
  );
};

export default AddItemButton;