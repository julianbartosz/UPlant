/**
 * MessageContainer Component
 * 
 * @file MessageContainer.jsx
 * @component
 * @param {Object} props
 * @param {Object|null} props.error - Error state with a message property.
 * @param {Object|null} props.success - Success state with a message property.
 * @returns {JSX.Element} The rendered MessageContainer component.
 * 
 * @example
 * <MessageContainer
 *   error={{ message: 'Failed to delete notification.' }}
 *   success={{ message: 'Notification deleted successfully!' }}
 * />
 * 
 * @remarks
 * - Displays error or success messages in a fixed-height container.
 * - Uses styles from `form.css` for consistent message appearance.
 * - Typically used in forms or tables to provide user feedback.
 */

import '../styles/form.css';

const MessageContainer = ({ error, success }) => {
  return (
    <div className="message-container">
      {error && <div className="message-error">{error.message}</div>}
      {success && <div className="message-success">{success.message}</div>}
    </div>
  );
};

export default MessageContainer;