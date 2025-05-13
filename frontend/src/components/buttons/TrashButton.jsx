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

