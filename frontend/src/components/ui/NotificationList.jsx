/**
 * @file NotificationList.jsx
 * @version 1.0.0
 * @description This component renders a list of notifications with sorting, filtering, and action capabilities.
 * 
 * @details
 * - The `NotificationList` component allows users to sort notifications by various fields, filter by task type or name, 
 *   and optionally display only today's notifications. It also provides actions to mark notifications as complete, skip them, 
 *   or view additional visual details.
 * 
 * @component
 * @param {Object} props - The props object.
 * @param {boolean} props.loading - Indicates whether the notifications are still loading.
 * @param {Array<Object>} props.notifications - The list of notification objects to display.
 * @param {Function} props.onComplete - Callback function triggered when a notification is marked as complete.
 * @param {Function} props.onSkip - Callback function triggered when a notification is skipped.
 * @param {Function} props.onShowVisual - Callback function triggered to display visual details of a notification.
 * 
 * @example
 * <NotificationList
 *   loading={false}
 *   notifications={[
 *     { instance_id: 1, name: 'Water Plants', type_display: 'Water', plant_names: ['Fern'], next_due: '2023-10-01' },
 *     { instance_id: 2, name: 'Fertilize Soil', type_display: 'Fertilize', plant_names: ['Cactus'], next_due: '2023-10-02' }
 *   ]}
 *   onComplete={(id) => console.log(`Complete notification with ID: ${id}`)}
 *   onSkip={(id) => console.log(`Skip notification with ID: ${id}`)}
 *   onShowVisual={(notification) => console.log('Show visual for:', notification)}
 * />
 */
import { useState } from 'react';
import { ThreeDots } from 'react-loader-spinner';
import './styles/notification-list.css';

const NotificationList = ({ loading, notifications, onComplete, onSkip, onShowVisual }) => {
  const [sortField, setSortField] = useState('next_due');
  const [sortOrder, setSortOrder] = useState('asc');
  const [filterType, setFilterType] = useState('');
  const [filterName, setFilterName] = useState('');
  const [showTodayOnly, setShowTodayOnly] = useState(false);

  const handleSort = (field) => {
    if (field === sortField) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const sortedNotifications = [...notifications]
    .filter((item) => {
      const dueDate = new Date(item.next_due);
      const today = new Date();
      const isToday =
        dueDate.getFullYear() === today.getFullYear() &&
        dueDate.getMonth() === today.getMonth() &&
        dueDate.getDate() === today.getDate();

      return (
        item.type_display.toLowerCase().includes(filterType.toLowerCase()) &&
        item.name.toLowerCase().includes(filterName.toLowerCase()) &&
        (!showTodayOnly || isToday)
      );
    })
    .sort((a, b) => {
      let valueA = a[sortField];
      let valueB = b[sortField];

      if (sortField === 'plant_names') {
        valueA = valueA.join(', ').toLowerCase();
        valueB = valueB.join(', ').toLowerCase();
      } else if (sortField === 'next_due') {
        valueA = new Date(valueA).getTime();
        valueB = new Date(valueB).getTime();
      } else if (typeof valueA === 'string') {
        valueA = valueA.toLowerCase();
        valueB = valueB.toLowerCase();
      }

      if (valueA == null) return sortOrder === 'asc' ? 1 : -1;
      if (valueB == null) return sortOrder === 'asc' ? -1 : 1;

      if (sortOrder === 'asc') {
        return valueA < valueB ? -1 : valueA > valueB ? 1 : 0;
      } else {
        return valueA > valueB ? -1 : valueA < valueB ? 1 : 0;
      }
    });

  return (
    <>
      <h1>DAILY REMINDERS</h1>
      <div className="controls">
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="filter-select"
        >
          <option value="">All Types</option>
          <option value="Water">Water</option>
          <option value="Fertilize">Fertilize</option>
          <option value="Prune">Prune</option>
          <option value="Harvest">Harvest</option>
          <option value="Other">Other</option>
          <option value="Weather">Weather</option>
        </select>
        <input
          type="text"
          placeholder="Filter by Task Name"
          value={filterName}
          onChange={(e) => setFilterName(e.target.value)}
          className="filter-input"
        />
        <label className="today-filter">
          <input
            type="checkbox"
            checked={showTodayOnly}
            onChange={(e) => setShowTodayOnly(e.target.checked)}
          />
          Show only today's notifications
        </label>
      </div>
      <>
        <table>
          <thead style={{ position: 'sticky', top: 0, zIndex: 1 }}>
            <tr>
              <th onClick={() => handleSort('name')}>
                Task Name {sortField === 'name' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('type_display')}>
                Type {sortField === 'type_display' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('plant_names')}>
                Plants {sortField === 'plant_names' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('next_due')}>
                Due Date {sortField === 'next_due' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th>Actions</th>
              <th>Visual</th>
            </tr>
          </thead>
          <tbody>
           {loading ? (
       <td colSpan={7} rowSpan={3} style={{ borderBottom: 'none'}}>
                  <div className="loading-spinner" 
                  style={{
                    width: '100%', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center'}}
                  >
                        <ThreeDots
                        visible={true}
                        height="80"
                        width="80"
                        color="white"
                        radius="9"
                        ariaLabel="three-dots-loading"
                        wrapperClass=""
                      />
                  </div>
                </td>
 
            ) : null}
              
            {!loading && sortedNotifications.length > 0 ? (
              sortedNotifications.map((notification) => (
                <tr key={notification.instance_id}>
                  <td>{notification.name}</td>
                  <td>{notification.type_display}</td>
                  <td className="plant-names">{notification.plant_names.map(
                    (plantName) => (
                      <li key={plantName} className="data-table-plant">
                        {plantName}
                      </li>
                    )
                  )}</td>
                  <td>{new Date(notification.next_due).toLocaleDateString()}</td>
                  {/* <td>{notification.interval}</td> */}
                  <td className="actions">
                    <button
                      className="btn complete"
                      style={{border: '2px solid black', marginRight: '10px'}}
                      onClick={() => onComplete(notification.instance_id)}
                    >
                      Complete
                    </button>
                    <button
                    style={{border: '2px solid black'}}
                      className="btn skip"
                      onClick={() => onSkip(notification.instance_id)}
                    >
                      Skip
                    </button>
                  </td>
                  <td className="visual">
                    <button
                    style={{border: '2px solid black'}}
                      className="btn visual-btn"
                      onClick={() => onShowVisual(notification)}
                    >
                      Show Visual
                    </button>
                    
                  </td>
                </tr>
              ))
            ) : !loading && (
              <tr>
                <td colSpan="7">
                ✅ Your garden has non pending reminders.
                </td>
                
              </tr>
            )}
          </tbody>
        </table>
      </>
    </>
  );
};

export default NotificationList;