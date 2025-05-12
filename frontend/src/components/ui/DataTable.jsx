/**
 * @file DataTable.jsx
 * @description A responsive data table component that displays notifications with CRUD operations.
 * This component renders notification data in a structured table format and provides functionality
 * for adding and removing notifications.
 * 
 * @component
 * @param {Object} props
 * @param {number} props.selectedGardenIndex - Index of the selected garden in the UserContext gardens array.
 * @param {Function} props.onAdd - Callback function to trigger adding a new notification.
 * @param {Function} [props.onEdit] - Callback function to trigger editing a notification, called with gardenIndex and notificationId.
 * @returns {JSX.Element} The rendered DataTable component.
 * 
 * @example
 * <DataTable
 *   selectedGardenIndex={0}
 *   onAdd={() => console.log('Add notification')}
 *   onEdit={(gardenIndex, notificationId) => console.log(`Edit notification ${notificationId} in garden ${gardenIndex}`)}
 * />
 * 
 * @details
 * - Content Structure:
 *   - The table displays notification data including name, type, plants, interval, and action controls
 *   - Each row represents a single notification with its associated properties
 *   - The first column shows the notification name
 *   - The type column displays a human-readable version of notification type codes (e.g., 'WA' to 'Water')
 *   - The plants column lists all plants associated with the notification
 *   - The days column shows the notification interval
 *   - The actions column contains controls for modifying or removing notifications
 * 
 * - Features:
 *   - Delete confirmation via modal dialog to prevent accidental removals
 *   - Empty state handling with a consistent UI for adding new notifications
 *   - Add button in a specially styled perspective row for visual emphasis
 *   - Type mapping to convert backend codes to user-friendly text
 *   - Integration with UserContext for state management
 *   - Proper error handling for API requests
 *   - Accessibility support with appropriate ARIA labels
 * 
 */
import { useContext, useState } from 'react';
import { AddItemButton, TrashButton } from '../buttons';
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

/**
 * DataTable component for displaying and managing notifications
 */
const DataTable = ({ selectedGardenIndex, onAdd }) => {
  const { gardens, dispatch, refreshCounts } = useContext(UserContext);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState(null);

  // Handlers for deletion flow
  const handleDeleteNotification = (gardenIndex, notificationId) => {
    setPendingDelete({ gardenIndex, notificationId });
    setIsModalOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!pendingDelete) return;

    const { gardenIndex, notificationId } = pendingDelete;
    const result = await deleteNotification(notificationId);

    if (result.success) {
      dispatch({ 
        type: 'REMOVE_NOTIFICATION', 
        garden_index: gardenIndex, 
        notification_id: notificationId 
      });
      
      if (DEBUG) console.log('Notification deleted successfully');
      refreshCounts();
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

  // Get notifications for the selected garden
  const notifications = gardens[selectedGardenIndex]?.notifications || [];

  // Render the add button row
  const renderAddButtonRow = () => (
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
  );

  return (
    <>
      <table className="data-table" role="grid">
        <caption style={{ backgroundColor: 'black' }}>
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
        
        <tbody>
          {notifications.length > 0 ? (
            <>
              {notifications.map((item) =>
                item && (
                  <tr key={item.id}>
                    <td className="name">{item.name}</td>
                    <td className="type">{mapNotificationType(item.type)}</td>
                    <td className="plants" style={{ textAlign: 'left' }}>
                      {item.plant_names?.map((plantName) => (
                        <li key={plantName} className="data-table-plant">
                          {plantName}
                        </li>
                      ))}
                    </td>
                    <td className="interval">{item.interval}</td>
                    <td className="data-table-actions">
                      <div>
                        <TrashButton
                          onClick={() => handleDeleteNotification(selectedGardenIndex, item.id)}
                          aria-label={`Delete notification ${item.name}`}
                        />
                      </div>
                    </td>
                  </tr>
                )
              )}
              {renderAddButtonRow()}
            </>
          ) : (
            renderAddButtonRow()
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