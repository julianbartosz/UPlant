import { FiPlus } from 'react-icons/fi';
import './styles/generic-btn.css';

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