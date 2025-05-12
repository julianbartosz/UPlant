/**
 * NotificationPage Component
 * 
 * @file NotificationPage.jsx
 * @version 1.0.0
 * @description A page component that displays notifications for a selected garden.
 * This component allows users to view, complete, skip, or visualize notifications related to their gardens.
 * 
 * @component
 * @returns {JSX.Element} The rendered NotificationPage component.
 * 
 * @remarks
 * - Fetches and displays notifications for a selected garden.
 * - Allows users to complete, skip, or visualize notifications.
 * - Uses context for garden data and custom hooks for content sizing.
 * - Visual mode highlights garden cells related to a notification.
 */

import { useRef, useEffect, useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { NavBar, GardenBar } from '../components/layout';
import { GardenGrid } from '../components/ui';
import { UserContext } from '../context/UserProvider';
import { NotificationList } from '../components/layout';
import { useContentSize } from '../hooks';
import { GridLoading } from '../components/widgets';
import { DEBUG, BASE_API } from '../constants';   
import './styles/notifications-page.css';

/**
 * Fetches notifications for a specific garden.
 * 
 * @param {string} gardenId - The ID of the garden to fetch notifications for.
 * @returns {Promise<{ success: boolean, data?: any, error?: string }>} The result of the API request.
 */
const fetchNotificationsByGarden = async (gardenId) => {
  if (DEBUG) {
    console.log('Fetching notifications for garden:', gardenId);
  }

  try {
    const response = await fetch(`${BASE_API}/notifications/notifications/by_garden/?garden_id=${gardenId}`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    
    // Filter for PENDING notifications
    const pendingNotifications = data
      .flatMap(garden => garden.notifications || [])
      .filter(notification => notification.status === 'PENDING');

    return { success: true, data: pendingNotifications };
  } catch (error) {
    console.error('Error fetching notifications:', error);
    return { success: false, error: error.message };
  }
};

/**
 * Completes or skips a notification instance.
 * 
 * @param {string} instanceId - The ID of the notification instance.
 * @param {string} action - The action to perform ('complete' or 'skip').
 * @returns {Promise<{ success: boolean, data?: any, error?: string }>}
 */
const processNotification = async (instanceId, action) => {
  if (DEBUG) {
    console.log(`Processing notification (${action}):`, instanceId);
  }

  try {
    const endpoint = `${BASE_API}/notifications/instances/${instanceId}/${action}/`;
    const response = await fetch(endpoint, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return { success: true, data: await response.json() };
  } catch (error) {
    console.error(`Error ${action} notification:`, error);
    return { success: false, error: error.message };
  }
};

// Add CSS styles for the visual controls
const visualControlsStyles = `
.visual-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background-color: rgba(0, 0, 0, 0.8);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: fixed;
  top: 88px;
  z-index: 100;

}

.btn {
  padding: 10px 20px;
  font-weight: 600;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  min-width: 120px;
  color: white;
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.btn.return {
  background-color: #4285F4;
}

.btn.return:hover {
  background-color: #3B73C5;
}

.btn.skip {
  background-color: #DB4437;
}

.btn.skip:hover {
  background-color: #C53929;
}

.btn.complete {
  background-color: #0F9D58;
}

.btn.complete:hover {
  background-color: #0B8043;
}

.visual-modal {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  align-items: center;
}

.notify-grid-container {
  margin-top: 20px;
  width: 100%;
  display: flex;
  justify-content: center;
}

.notification-list-container {
  border: 2px solid black;
  width: 100%;
  height: calc(100% - 148px);
  margin-bottom: 30px;
  border-radius: 8px;
  overflow-y: auto;
  background: linear-gradient(to bottom right, rgba(152, 152, 152, 0.6), rgba(65, 64, 64, 0.6));
  padding: 20px;
  margin-right: 30px;
  margin-left: 30px;
}
`;

function NotificationPage() {
  const navigate = useNavigate();
  const { gardens, loading: globalLoading } = useContext(UserContext);

  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedGardenIndex, setSelectedGardenIndex] = useState(0);
  const [toggleVisual, setToggleVisual] = useState(false);
  const [coloredCells, setColoredCells] = useState(new Set());
  const [selectedInstance, setSelectedInstance] = useState(null);

  const containerRef = useRef(null);
  const contentSize = useContentSize(containerRef);

  // Inject styles on component mount
  useEffect(() => {
    const styleEl = document.createElement('style');
    styleEl.innerHTML = visualControlsStyles;
    document.head.appendChild(styleEl);
    
    return () => {
      document.head.removeChild(styleEl);
    };
  }, []);

  // Fetch notifications when garden selection or gardens change
  useEffect(() => {
    const loadNotifications = async () => {
      setLoading(true);
      setError(null);
      
      const gardenId = gardens[selectedGardenIndex]?.id;
      if (!gardenId) {
        setError('No garden selected.');
        setLoading(false);
        return;
      }

      const result = await fetchNotificationsByGarden(gardenId);
      if (result.success) {
        setNotifications(result.data);
      } else {
        setError('Failed to load notifications. Please try again later.');
      }
      
      setLoading(false);
    };

    loadNotifications();
  }, [selectedGardenIndex, gardens]);

  const handleComplete = async (instanceId) => {
    try {
      const result = await processNotification(instanceId, 'complete');
      if (result.success) {
        refreshNotifications();
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      alert(`Failed to complete notification: ${error.message}`);
    }
    
    resetVisualMode();
  };

  const handleSkip = async (instanceId) => {
    try {
      const result = await processNotification(instanceId, 'skip');
      if (result.success) {
        refreshNotifications();
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      alert(`Failed to skip notification: ${error.message}`);
    }
    
    resetVisualMode();
  };

  const handleShowVisual = (instance) => {
    if (!instance) return;
    
    const garden = gardens[selectedGardenIndex];
    if (!garden) return;

    const coloredCellsSet = new Set();
    const plantNames = instance.plant_names;
    
    garden.cells.forEach((row, i) => {
      row.forEach((cell, j) => {
        if (cell && plantNames.some(p => p === (cell.common_name || cell.plant_detail.name))) {
          coloredCellsSet.add(`${i}-${j}`);
        }
      });
    });
    
    setSelectedInstance(instance.instance_id);
    setColoredCells(coloredCellsSet);
    setToggleVisual(true);
  };

  const refreshNotifications = async () => {
    const gardenId = gardens[selectedGardenIndex]?.id;
    if (!gardenId) return;
    
    const result = await fetchNotificationsByGarden(gardenId);
    if (result.success) {
      setNotifications(result.data);
    }
  };

  const resetVisualMode = () => {
    setToggleVisual(false);
    setSelectedInstance(null);
    setColoredCells(new Set());
  };

  if (globalLoading) {
    return <GridLoading />;
  }

  if (error) {
    return (
      <div style={{ 
        width: '100vw', 
        height: '100vh', 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center' 
      }}>
        <div>{error}</div>
      </div>
    );
  }

  return (
    <div className="notification-page-container">
      <NavBar
        title="Notifications"
        buttonOptions={['back']}
        onBack={() => navigate('/dashboard')}
      />
      <div className="notification-content-container" ref={containerRef}>
        {toggleVisual ? (
          <div className="visual-modal">
            {/* Visual controls at the top of the container */}
            <div className="visual-controls">
              <button 
                className="btn return"
                onClick={() => resetVisualMode()}
              >
                Return
              </button>
              <button 
                className="btn skip"
                onClick={() => handleSkip(selectedInstance)}
              >
                Skip
              </button>
              <button 
                className="btn complete"
                onClick={() => handleComplete(selectedInstance)}
              >
                Complete
              </button>
            </div>
            <div className="notify-grid-container">
              <GardenGrid
                coloredCells={coloredCells}
                interactive={false}
                selectedGardenIndex={selectedGardenIndex}
                contentSize={contentSize}
              />
            </div>
          
          </div>
        ) : (
          <>
            <GardenBar
              selectedGardenIndex={selectedGardenIndex}
              setSelectedGardenIndex={setSelectedGardenIndex}
              dynamic={false}
              centered={true}
            />
            <div className="notification-list-container">
              <NotificationList 
                loading={loading}
                notifications={notifications}
                onComplete={handleComplete}
                onSkip={handleSkip}
                onShowVisual={handleShowVisual}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default NotificationPage;