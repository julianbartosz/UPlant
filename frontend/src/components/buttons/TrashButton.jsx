/**
 * DeleteButton Component
 * 
 * @file DeleteButton.jsx
 * @component
 * @param {Object} props
 * @param {Function} props.onClick - Callback function to handle button click.
 * @param {string} props.ariaLabel - Accessibility label for the button.
 * @param {string} [props.className] - Additional CSS class for styling.
 * @param {boolean} [props.disabled=false] - Whether the button is disabled.
 * @returns {JSX.Element} The rendered DeleteButton component.
 * 
 * @example
 * <DeleteButton
 *   onClick={() => console.log('Delete clicked')}
 *   ariaLabel="Delete notification"
 * />
 * 
 * @remarks
 * - Renders a button with a remove icon for deletion actions.
 * - Uses styles from `buttons.css` for consistent appearance with other buttons (e.g., EditButton, AddButton).
 * - Designed for use in tables or forms, such as the DataTable component.
 * - Includes accessibility features via `aria-label`.
 */

import { FiTrash2 } from 'react-icons/fi';
import './styles/fancy-btn.css';

const TrashButton = ({ onClick, ariaLabel, className = '', disabled = false }) => {
  return (
    <button
      onClick={onClick}
      aria-label={ariaLabel}
      className={`remove-button ${className}`}
      disabled={disabled}
    >
      <FiTrash2 />
    </button>
  );
};

export default TrashButton;

