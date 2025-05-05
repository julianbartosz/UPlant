/**
 * DataTable Component
 * 
 * @file DataTable.jsx
 * @component
 * @param {Object} props
 * @param {number} props.selectedGardenIndex - Index of the selected garden in the UserContext gardens array.
 * @param {Function} props.onAdd - Callback function to trigger adding a new notification.
 * @param {Function} props.onEdit - Callback function to trigger editing a notification, called with gardenIndex and notificationId.
 * @returns {JSX.Element} The rendered DataTable component.
 * 
 * @example
 * <DataTable
 *   selectedGardenIndex={0}
 *   onAdd={() => console.log('Add notification')}
 *   onEdit={(gardenIndex, notificationId) => console.log(`Edit notification ${notificationId} in garden ${gardenIndex}`)}
 * />
 * 
 * @remarks
 * - Displays a table of notifications from the selected garden, including name, type, plants, and actions.
 * - The `type` field is mapped to human-readable labels (e.g., `WA` to `Water`).
 * - Allows adding notifications via an Add button in a styled perspective row (spanning all columns) or empty state, triggering the `onAdd` callback.
 * - Allows editing and deleting notifications via Edit and Delete buttons in the Actions column.
 * - Uses a ConfirmModal component for delete confirmation, replacing native window.confirm.
 * - Shows an empty state with a notification icon, a cursive, tilted message, and an Add button when no notifications exist.
 * - Uses `data-table.css` for styling the table, perspective row, empty state, and modal, and `buttons.css` for button styles.
 * - Debug logging is controlled by `VITE_DEBUG` from constants.
 * - Errors are logged to the console without UI feedback, as this is not a form.
 */

import { useContext, useState } from 'react';
import { AddItemButton, EditButton, TrashButton } from '../buttons';
import { FiBell } from 'react-icons/fi';
import { UserContext } from '../../context/UserProvider';
import { BASE_API, DEBUG } from '../../constants';
import ConfirmModal from '../modals/ConfirmModal';
import './styles/data-table.css';

/**
 * Maps notification type codes to human-readable labels.
 * 
 * @param {string} type - The notification type code (e.g., 'WA').
 * @returns {string} The human-readable label (e.g., 'Water').
 */
const mapNotificationType = (type) => {
  const typeMap = {
    WA: 'Water',
    FE: 'Fertilize',
    PR: 'Prune',
    HA: 'Harvest',
    OT: 'Other',
    WE: 'Weather',
  };
  return typeMap[type] || type;
};

/**
 * Performs the notification deletion API request.
 * 
 * @param {string} notificationId - The ID of the notification to delete.
 * @returns {Promise<{ success: boolean|null, error?: any }>} The result of the API request.
 */
const deleteNotification = async (notificationId) => {
  try {
    const url = `${BASE_API}/notifications/notifications/${notificationId}/`;
    if (DEBUG) console.log(`Deleting notification at ${url}`);

    const response = await fetch(url, {
      method: 'DELETE',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      return { success: true };
    }
    const errorData = await response.json();
    return { success: false, error: errorData };
  } catch (error) {
    return { success: null, error: error.message };
  }
};

const DataTable = ({ selectedGardenIndex, onAdd, onEdit }) => {
  const { gardens, dispatch } = useContext(UserContext);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState(null);

  const handleDeleteNotification = async (gardenIndex, notificationId) => {
    setPendingDelete({ gardenIndex, notificationId });
    setIsModalOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!pendingDelete) return;

    const { gardenIndex, notificationId } = pendingDelete;
    const result = await deleteNotification(notificationId);

    if (result.success) {
      dispatch({ type: 'REMOVE_NOTIFICATION', garden_index: gardenIndex, notification_id: notificationId });
      if (DEBUG) console.log('Notification deleted successfully');
    } else if (result.success === null) {
      console.error('Network error:', result.error);
    } else {
      console.error('Failed to delete notification:', result.error);
    }

    setIsModalOpen(false);
    setPendingDelete(null);
  };

  const handleCancelDelete = () => {
    setIsModalOpen(false);
    setPendingDelete(null);
  };

  const notifications = gardens[selectedGardenIndex]?.notifications || [];

  return (
    <>
    
      <table className="data-table" role="grid">
      <caption style={{backgroundColor: 'black'}}>
      🔔 Configure your maintenance / care routine 🔔
  </caption>
        <thead className="data-table-header">
          <tr>
            <th>Name</th>
            <th>Type</th>
            <th>Plants</th>
            <th>Days</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody >
          {notifications.length > 0 ? (
            <>
              {notifications.map((item) =>
                item && (
                  <tr key={item.id} >
                    <td className='name'>{item.name}</td>
                    <td className="type">{mapNotificationType(item.type)}</td>
                    <td className='plants' style= {{textAlign: 'left'}}>
                      {item.plant_names?.map((plantName) => (
                        <li key={plantName} className="data-table-plant">
                        {plantName}
                    </li>
                      ))}
                    </td>
                    <td className='interval'>
                      {item.interval}
                    </td>
                    <td className='data-table-actions'>
                      <div>
                        {/* <EditButton
                          onClick={() => onEdit(selectedGardenIndex, item.id)}
                          aria-label={`Edit notification ${item.name}`}
                        /> */}
                        <TrashButton
                          onClick={() => handleDeleteNotification(selectedGardenIndex, item.id)}
                          aria-label={`Delete notification ${item.name}`}
                        />
                      </div>
                    </td>
                  </tr>
                )
              )}
              <tr aria-label="Add new notification row">
                <td colSpan={5} className="data-table-add-action">
                  <div className="data-table-add-content">
                    <AddItemButton
                      onClick={onAdd}
                      ariaLabel="Add new recurring reminder"
                      className="data-table-add-button"
                    />
                  </div>
                </td>
              </tr>
  
            </>
          ) : (
            <tr aria-label="Add new notification row">
                <td colSpan={5} className="data-table-add-action">
                  <div className="data-table-add-content">
                    <AddItemButton
                      onClick={onAdd}
                      ariaLabel="Add new recurring reminder"
                      className="data-table-add-button"
                    />
                  </div>
                </td>
              </tr>
          )}
        </tbody>
      </table>
    
    <ConfirmModal
    isOpen={isModalOpen}
    onConfirm={handleConfirmDelete}
    onCancel={handleCancelDelete}
    message="Are you sure you want to delete this notification?"
  />
  </>
  );
};

export default DataTable;