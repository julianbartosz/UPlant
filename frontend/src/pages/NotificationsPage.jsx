/**
 * NotificationPage Component
 * 
 * @file NotificationPage.jsx
 * @component
 * @returns {JSX.Element} The rendered NotificationPage component.
 * 
 * @example
 * <NotificationPage />
 * 
 * @remarks
 * - Fetches and displays notifications for a selected garden.
 * - Allows users to complete, skip, or visualize notifications.
 * - Uses context for garden data and custom hooks for content sizing.
 * - Visual mode highlights garden cells related to a notification.
 */

import { 
  useRef, 
  useEffect, 
  useState, 
  useContext 
} from 'react';
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
    console.log('--- Fetch Notifications Request ---');
    console.log('Garden ID:', gardenId);
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
    if (!data) {
      throw new Error('No data received');
    }

    if (DEBUG) {
      console.log('Fetched notifications data:', data);
    }

    // Flatten notifications and filter for PENDING status
    const flattenedNotifications = data
      .flatMap(garden => garden.notifications || [])
      .filter(notification => notification.status === 'PENDING');

    return { success: true, data: flattenedNotifications };
  } catch (error) {
    if (DEBUG) {
      console.error('Error fetching notifications:', error);
    }
    return { success: false, error: error.message };
  }
};

/**
 * Completes a notification instance.
 * 
 * @param {string} instanceId - The ID of the notification instance to complete.
 * @returns {Promise<{ success: boolean, data?: any, error?: string }>} The result of the API request.
 */
const completeNotification = async (instanceId) => {
  if (DEBUG) {
    console.log('--- Complete Notification Request ---');
    console.log('Instance ID:', instanceId);
  }

  try {
    const response = await fetch(`${BASE_API}/notifications/instances/${instanceId}/complete/`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    if (DEBUG) {
      console.log('Complete notification response:', data);
    }

    return { success: true, data };
  } catch (error) {
    if (DEBUG) {
      console.error('Error completing notification:', error);
    }
    return { success: false, error: error.message };
  }
};

/**
 * Skips a notification instance.
 * 
 * @param {string} instanceId - The ID of the notification instance to skip.
 * @returns {Promise<{ success: boolean, data?: any, error?: string }>} The result of the API request.
 */
const skipNotification = async (instanceId) => {
  if (DEBUG) {
    console.log('--- Skip Notification Request ---');
    console.log('Instance ID:', instanceId);
  }

  try {
    const response = await fetch(`${BASE_API}/notifications/instances/${instanceId}/skip/`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    if (DEBUG) {
      console.log('Skip notification response:', data);
    }

    return { success: true, data };
  } catch (error) {
    if (DEBUG) {
      console.error('Error skipping notification:', error);
    }
    return { success: false, error: error.message };
  }
};

function NotificationPage() {
  const navigate = useNavigate();
  const { gardens, loading: globalLoading } = useContext(UserContext);

  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [squareSize, setSquareSize] = useState(1);
  const [fontSize, setFontSize] = useState(null);
  const [selectedGardenIndex, setSelectedGardenIndex] = useState(0);
  const [selectedEmptyCells, setDugCells] = useState(new Set());
  const [selectedPlantCells, setSelectedPlantCells] = useState(new Set());
  const [toggleVisual, setToggleVisual] = useState(false);
  const [coloredCells, setColoredCells] = useState(new Set());
  const [selectedInstance, setSelectedInstance] = useState(null);

  const containerRef = useRef(null);
  const contentSize = useContentSize(containerRef);
  const selectedEmptyCellsRef = useRef(selectedEmptyCells);
  const selectedPlantCellsRef = useRef(selectedPlantCells);
  const selectedGardenIndexRef = useRef(selectedGardenIndex);

  useEffect(() => {
    selectedEmptyCellsRef.current = selectedEmptyCells;
  }, [selectedEmptyCells]);

  useEffect(() => {
    selectedPlantCellsRef.current = selectedPlantCells;
  }, [selectedPlantCells]);

  useEffect(() => {
    selectedGardenIndexRef.current = selectedGardenIndex;
  }, [selectedGardenIndex]);

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
    if (DEBUG) {
      console.log('--- handleComplete ---');
      console.log('Instance ID:', instanceId);
    }
    try {
      const result = await completeNotification(instanceId);
      if (!result.success) {
        throw new Error(result.error);
      }
      const fetchResult = await fetchNotificationsByGarden(gardens[selectedGardenIndex]?.id);
      if (fetchResult.success) {
        setNotifications(fetchResult.data);
      }
    } catch (error) {
      alert(`Failed to complete notification: ${error.message}`);
    }
    setToggleVisual(false);
    setSelectedInstance(null);
  };

  const handleSkip = async (instanceId) => {
    if (DEBUG) {
      console.log('--- handleSkip ---');
      console.log('Instance ID:', instanceId);
    }
    try {
      const result = await skipNotification(instanceId);
      if (!result.success) {
        throw new Error(result.error);
      }
      const fetchResult = await fetchNotificationsByGarden(gardens[selectedGardenIndex]?.id);
      if (fetchResult.success) {
        setNotifications(fetchResult.data);
      }
    } catch (error) {
      alert(`Failed to skip notification: ${error.message}`);
    }
    setToggleVisual(false);
    setSelectedInstance(null);
  };

  const handleShowVisual = (instance) => {
    if (DEBUG) {
      console.log('--- handleShowVisual ---');
      console.log('Instance:', instance);
    }
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
    
    if (DEBUG) {
      console.log('Colored cells:', coloredCellsSet);
    }
    setSelectedInstance(instance.instance_id);
    setColoredCells(coloredCellsSet);
    setToggleVisual(true);
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
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              flexDirection: 'column',
              alignItems: 'center',
              marginBottom: '10px',
              gap: '8px'
            }}>
              <button
                style={{
                  width: '120px',
                  padding: '8px 16px',
                  background: 'blue',
                  color: 'white',
                  border: '2px solid #333',
                  borderRadius: '6px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'background 0.2s'
                }}
                onClick={() => setToggleVisual(false)}
                onMouseOver={(e) => e.target.style.background = '#3B4A8A'}
                onMouseOut={(e) => e.target.style.background = 'blue'}
              >
                Return
              </button>
              <button
                style={{
                  width: '120px',
                  padding: '8px 16px',
                  background: 'red',
                  color: 'white',
                  border: '2px solid #333',
                  borderRadius: '6px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'background 0.2s'
                }}
                className="btn skip"
                onClick={() => { handleSkip(selectedInstance); }}
                onMouseOver={(e) => e.target.style.background = '#E55A5A'}
                onMouseOut={(e) => e.target.style.background = 'red'}
              >
                Skip
              </button>
              <button
                style={{
                  width: '120px',
                  padding: '8px 16px',
                  background: 'green',
                  color: 'white',
                  border: '2px solid #333',
                  borderRadius: '6px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'background 0.2s'
                }}
                className="btn complete"
                onClick={() => { handleComplete(selectedInstance); }}
                onMouseOver={(e) => e.target.style.background = '#27AE60'}
                onMouseOut={(e) => e.target.style.background = 'green'}
              >
                Complete
              </button>
            </div>
            <GardenGrid
              coloredCells={coloredCells}
              interactive={false}
              gardens={gardens}
              selectedGardenIndex={selectedGardenIndex}
              setSelectedGardenIndex={setSelectedGardenIndex}
              squareSize={squareSize}
              fontSize={fontSize}
              contentSize={contentSize}
              selectedEmptyCells={selectedEmptyCellsRef.current}
              selectedPlantCells={selectedPlantCellsRef.current}
            />
          </div>
        ) : (
          <>
            <div>
              <GardenBar
                selectedGardenIndex={selectedGardenIndex}
                setSelectedGardenIndex={setSelectedGardenIndex}
                onAdd={() => setToggleVisual(!toggleVisual)}
                dynamic={false}
                centered={true}
              />
            </div>
            <div style={{
                border: '2px solid black', 
                justifyContent: 'center', 
                alignItems: 'center', 
                width: '100vw', 
                alignSelf: 'end', 
                height: 'calc(100% - 148px)', 
                marginBottom: '30px', 
                borderRadius: '8px', 
                overflowY: 'scroll', 
                background: 'linear-gradient(to bottom right, rgba(152, 152, 152, 0.6), rgba(65, 64, 64, 0.6))',
                padding: '20px',
                marginRight: '30px',
                marginLeft: '30px',
            }}>
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