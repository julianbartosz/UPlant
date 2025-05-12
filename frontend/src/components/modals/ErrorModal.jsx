/**
 * @file ErrorModal.jsx
 * @description A reusable error modal component for displaying error messages.
 */
import { useEffect, useRef } from 'react';
import { DEBUG } from '../../constants';
import './styles/generic-modal.css';

const ErrorModal = ({ isOpen, onClose, message }) => {
  const okButtonRef = useRef(null);

  useEffect(() => {
    if (isOpen && okButtonRef.current) {
      okButtonRef.current.focus();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleClose = () => {
    if (DEBUG) {
      console.log('--- ErrorModal handleClose ---');
    }
    onClose();
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="modal-message">
      <div className="modal-container">
        <p id="modal-message" className="modal-message">{message}</p>
        <div className="modal-actions">
          <button
            className="modal-confirm-button"
            onClick={handleClose}
            ref={okButtonRef}
          >
            OK
          </button>
        </div>
      </div>
    </div>
  );
};

export default ErrorModal;