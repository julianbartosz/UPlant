/**
 * ErrorModal Component
 * 
 * @file ErrorModal.jsx
 * @component
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether the modal is visible.
 * @param {Function} props.onClose - Callback to execute when the OK button is clicked.
 * @param {string} props.message - The error message to display.
 * 
 * @returns {JSX.Element|null} The rendered ErrorModal component or null if not open.
 * 
 * @example
 * <ErrorModal
 *   isOpen={true}
 *   onClose={() => console.log('Modal closed')}
 *   message="An error occurred while processing your request."
 * />
 * 
 * @remarks
 * - Displays an error message with a single OK button to dismiss the modal.
 * - Styled consistently with ConfirmModal, using the same CSS classes and layout.
 * - Implements focus management to focus the OK button when the modal opens.
 * - Includes ARIA attributes for accessibility.
 * - Supports DEBUG logging for user interactions.
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