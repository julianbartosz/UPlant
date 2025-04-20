import { useRef, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useNotifications, useGardens, useUser } from '../hooks';
import { NavBar, GardenBar } from '../components/layout';
import { GardenGrid } from '../components/ui';
import './styles/notifications-page.css';

function NotificationPage() {
    const { username, usernameError } = useUser();
    const { notificationsList, notificationsListLoading, notificationsListError } = useNotifications();
    const { gardens, gardensLoading, gardensError } = useGardens();

    const navigate = useNavigate();
    const [squareSize, setSquareSize] = useState(1);
    const [fontSize, setFontSize] = useState(null);
    const [selectedGardenIndex, setSelectedGardenIndex] = useState(0);
    const [selectedEmptyCells, setDugCells] = useState(new Set());
    const [selectedPlantCells, setSelectedPlantCells] = useState(new Set());
    const [contentSize, setContentSize] = useState(500);

    const containerRef = useRef(null);
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
        setDugCells(new Set());
        setSelectedPlantCells(new Set());

        const handleResize = () => {
            if (containerRef.current) {
                const { width, height } = containerRef.current.getBoundingClientRect();
                const maxDimension = Math.max(gardens[selectedGardenIndex].x, gardens[selectedGardenIndex].y);
                const newSquareSize = Math.min(width * 0.6, height * 0.6) / maxDimension;
                setFontSize(newSquareSize * 0.5);
                setContentSize(height - 88);
                setSquareSize(newSquareSize);
            }
        };

        handleResize();
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [selectedGardenIndex, gardens]);

    useEffect(() => {
        const observer = new MutationObserver(() => {
            setFontSize((prevFontSize) => prevFontSize + 0);
        });

        if (containerRef.current) {
            observer.observe(containerRef.current, { childList: true, subtree: true });
        }

        return () => observer.disconnect();
    }, []);

    if (notificationsListLoading) return <p>Loading notificationsList...</p>;
    if (gardensLoading) return <p>Loading gardens...</p>;
    if (!gardens) return <p>No gardens available.</p>;

    if (gardensError || notificationsListError || usernameError) {
        console.error('Error fetching data:', gardensError, notificationsListError, usernameError);
        return <p>Error fetching data.</p>;
    }

    const handleNotificationClick = (plants) => {
        const garden = { ...gardens[selectedGardenIndex]};
        const redCells = new Set();

        garden.cells.forEach((row, i) => {
            row.forEach((cell, j) => {
                if (cell && plants.some(p => p.id === cell.id)) {
                    redCells.add(`${i}-${j}`);
                }
            });
        });
        console.log('Red cells:', redCells);
        setSelectedPlantCells(redCells);
    };

    return (
        <div className="notification-page-container">
            <NavBar
                title="Notifications"
                buttonOptions={['back']}
                username={username}
                onBack={() => navigate('/dashboard')}
            />
            <div className="notification-content-container">
                <div className="garden-container-static" ref={containerRef}>
                        <GardenBar 
                            dynamic={false} 
                            selectedGardenIndex={selectedGardenIndex} 
                            setSelectedGardenIndex={setSelectedGardenIndex} 
                            style={{justifyContent: 'center'}} 
                        />
                    <div className="notification-buttons">
                        {notificationsList[selectedGardenIndex]?.map((notification, index) => (
                            <button
                                key={index}
                                onClick={() => handleNotificationClick(notification.plants)}
                                className="notification-button"
                            >
                                {notification.name}
                            </button>
                        ))}
                    </div>
                    <GardenGrid
                        interactive={false}
                        garden={gardens[selectedGardenIndex]}
                        fontSize={fontSize}
                        squareSize={squareSize}
                        contentSize={contentSize}
                        coloredCells={selectedPlantCells}
                    />
                </div>
            </div>
        </div>
    );
}

export default NotificationPage;