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