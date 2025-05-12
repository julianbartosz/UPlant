/**
 * EditButton Component
 * 
 * @file EditButton.jsx
 * @component
 * @param {Object} props
 * @param {Function} props.onClick - Callback function to handle button click.
 * @param {string} props.ariaLabel - Accessibility label for the button.
 * @param {string} [props.className] - Additional CSS class for styling.
 * @param {boolean} [props.disabled=false] - Whether the button is disabled.
 * @returns {JSX.Element} The rendered EditButton component.
 * 
 * @example
 * <EditButton
 *   onClick={() => console.log('Edit clicked')}
 *   ariaLabel="Edit notification"
 * />
 * 
 * @remarks
 * - Renders a button with an edit icon for editing actions.
 * - Uses styles from `buttons.css` for consistent appearance with other buttons.
 * - Designed for use in tables or forms, such as the DataTable component.
 * - Includes accessibility features via `aria-label`.
 */

import { FiEdit } from 'react-icons/fi';
import './styles/fancy-btn.css';

const EditButton = ({ onClick, ariaLabel, className = '', disabled = false }) => {
  return (
    <button
      onClick={onClick}
      aria-label={ariaLabel}
      className={`edit-button ${className}`}
      disabled={disabled}
    >
      <FiEdit />
    </button>
  );
};

export default EditButton;