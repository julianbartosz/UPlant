import { useRef, useEffect, useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { NavBar, GardenBar } from '../components/layout';
import { GardenGrid } from '../components/ui';

import './styles/notifications-page.css';
import { UserContext } from '../context/UserProvider';
import { NotificationList } from '../components/layout';
import { useContentSize } from '../hooks';
import { BackButton, GenericButton } from '../components/buttons';
import { Grid } from 'react-loader-spinner';
import { GridLoading } from '../components/widgets';


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

  useEffect(() => {
    const observer = new MutationObserver(() => {
      setFontSize((prevFontSize) => prevFontSize + 0);
    });

    if (containerRef.current) {
      observer.observe(containerRef.current, { childList: true, subtree: true });
    }

    return () => observer.disconnect();
  }, []);


  // Fetch notifications by garden
  const fetchNotifications = async () => {
    setLoading(true);
    setError(null);
    const gardenId = gardens[selectedGardenIndex]?.id;
    if (!gardenId) {
      setError('No garden selected.');
      setLoading(false);
      return;
    }
    try {
      const response = await fetch(`http://localhost:8000/api/notifications/notifications/by_garden/?garden_id=${gardenId}`, {
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
      console.log('Fetched notifications:', data);
      if (!data) {
        throw new Error('No data received');
      }

      // Flatten notifications and filter for PENDING status
      const flattenedNotifications = data
        .flatMap(garden => garden.notifications || [])
        .filter(notification => notification.status === 'PENDING');
      setNotifications(flattenedNotifications);
    } catch (error) {
      console.error('Error fetching notifications:', error);
      setError('Failed to load notifications. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [selectedGardenIndex, gardens]);

  if (loading || globalLoading) {
    return (
      <GridLoading />
    );
  }

  const completeNotification = async (instanceId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/notifications/instances/${instanceId}/complete/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!response.ok) throw new Error(`Failed to complete notification. Status: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Error completing notification:', error);
      throw error;
    }
  };

  const skipNotification = async (instanceId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/notifications/instances/${instanceId}/skip/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!response.ok) throw new Error(`Failed to skip notification. Status: ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Error skipping notification:', error);
      throw error;
    }
  };

  const handleComplete = async (instanceId) => {
    try {
      await completeNotification(instanceId);
      await fetchNotifications();
    } catch (error) {
      alert(`Failed to complete notification: ${error.message}`);
    }
  };

  const handleSkip = async (instanceId) => {
    try {
      await skipNotification(instanceId);
      await fetchNotifications();
    } catch (error) {
      alert(`Failed to skip notification: ${error.message}`);
    }
  };

  const handleShowVisual = (plantNames) => {
    const garden = gardens[selectedGardenIndex];
    if (!garden) return;

    const coloredCellsSet = new Set();
    garden.cells.forEach((row, i) => {
      row.forEach((cell, j) => {
        if (cell && plantNames.some(p => p === (cell.common_name || cell.plant_detail.name))) {
          coloredCellsSet.add(`${i}-${j}`);
        }
      });
    });

    setColoredCells(coloredCellsSet);
    setToggleVisual(true);
  };

  if (error) {
    return (
      <div style={{ width: '100vw', height: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
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
            <GenericButton label="Return" style={{marginBottom: "20px"}} onClick={() => setToggleVisual(false)} />
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
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '10%' }}>
              <GardenBar
                selectedGardenIndex={selectedGardenIndex}
                setSelectedGardenIndex={setSelectedGardenIndex}
                onAdd={() => setToggleVisual(!toggleVisual)}
                dynamic={false}
                centered={true}
              />
            </div>
            <NotificationList
              notifications={notifications}
              onComplete={handleComplete}
              onSkip={handleSkip}
              onShowVisual={handleShowVisual}
            />
          </>
        )}
      </div>
    </div>
  );
}

export default NotificationPage;