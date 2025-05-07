/**
 * ConfirmModal Component
 * 
 * @param {Object} props
 * @param {boolean} props.isOpen - Whether the modal is visible.
 * @param {Function} props.onConfirm - Callback to execute on confirm.
 * @param {Function} props.onCancel - Callback to execute on cancel.
 * @param {string} props.message - The confirmation message to display.
 * @returns {JSX.Element|null} The rendered modal or null if not open.
 */

import { useEffect, useRef } from "react";
import "./styles/generic-modal.css";

const ConfirmModal = ({ isOpen, onConfirm, onCancel, message }) => {
    const confirmButtonRef = useRef(null);
  
    useEffect(() => {
      if (isOpen && confirmButtonRef.current) {
        confirmButtonRef.current.focus();
      }
    }, [isOpen]);
  
    if (!isOpen) return null;
  
    return (
      <div className="modal-overlay" role="dialog" aria-modal="true" aria-labelledby="modal-message">
        <div className="modal-container">
          <p id="modal-message" className="modal-message">{message}</p>
          <div className="modal-actions">
            <button className="modal-confirm-button" onClick={onConfirm} ref={confirmButtonRef}>
              Confirm
            </button>
            <button className="modal-cancel-button" onClick={onCancel}>
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  };

  export default ConfirmModal;