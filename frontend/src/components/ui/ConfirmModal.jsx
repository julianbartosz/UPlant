const ConfirmModal = ({ isOpen, onConfirm, onCancel, message }) => (
    isOpen && (
      <div className="modal">
        <p>{message}</p>
        <button onClick={onConfirm}>Confirm</button>
        <button onClick={onCancel}>Cancel</button>
      </div>
    )
  );