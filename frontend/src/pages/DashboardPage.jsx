import { useRef, useEffect, useState } from 'react';
import { useGardens, useUser } from '../hooks';
import { GardenGrid } from '../components/ui';
import { NotificationSection, GardenBar, PlantSearchSideBar, NavBar } from '../components/layout';
import { GridLoading } from '../components/widgets';
import './styles/dashboard-page.css';

function DashboardPage() {

  const { username } = useUser();
  const { gardens, mediateAddPlantToGarden, mediateRemovePlantFromGarden } = useGardens();
  const [squareSize, setSquareSize] = useState(1);
  const [fontSize, setFontSize] = useState(null);
  const [selectedGardenIndex, setSelectedGardenIndex] = useState(0);
  const [selectedEmptyCells, setSelectedEmptyCells] = useState(new Set());
  const [selectedPlantCells, setSelectedPlantCells] = useState(new Set());
  const [contentSize, setContentSize] = useState(0);

  const containerRef = useRef(null);
  const selectedGardenIndexRef = useRef(selectedGardenIndex);
  const selectedEmptyCellsRef = useRef(selectedEmptyCells);
  const selectedPlantCellsRef = useRef(selectedPlantCells);

  useEffect(() => {
    selectedGardenIndexRef.current = selectedGardenIndex;
    setSelectedEmptyCells(new Set());
    setSelectedPlantCells(new Set());
     
    const handleResize = () => {
      if (containerRef.current && gardens && gardens.length > 0) {

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

  useEffect(() => { selectedEmptyCellsRef.current = selectedEmptyCells; }, [selectedEmptyCells]);
  useEffect(() => { selectedPlantCellsRef.current = selectedPlantCells; }, [selectedPlantCells]);

  useEffect(() => {
    const observer = new MutationObserver(() => {
      setFontSize((prevFontSize) => prevFontSize + 0);
    });
    if (containerRef.current) observer.observe(containerRef.current, { childList: true, subtree: true });
    return () => { if (containerRef.current) observer.disconnect(); };
  }, []);


  const handlePlantClick = (item) => {
    if (item.type === 'SHEAR') {
      selectedPlantCellsRef.current.forEach(key => {
        const [row, col] = key.split('-').map(Number);
        if (row < gardens[selectedGardenIndexRef.current].y && col < gardens[selectedGardenIndexRef.current].x) mediateRemovePlantFromGarden(gardens[selectedGardenIndexRef.current].id, row, col);
      });
      return;
      
    }

    const currentGarden = gardens[selectedGardenIndexRef.current]
      selectedEmptyCellsRef.current.forEach(key => {
        const [row, col] = key.split('-').map(Number);
        console.log("ROW COL: ", row, col);
        if (row < currentGarden.y && col < currentGarden.x) mediateAddPlantToGarden(selectedGardenIndexRef.current, item, row, col);
      });
  };

  const cellClickHandler = (obj, i, j) => {
    const isTaken = obj !== null;
    const key = `${i}-${j}`;

    if (!isTaken) {
      const newSet = new Set(selectedEmptyCells);
      newSet.has(key) ? newSet.delete(key) : newSet.add(key);
      setSelectedEmptyCells(newSet);
    } else {
      const newSet = new Set(selectedPlantCells);
      newSet.has(key) ? newSet.delete(key) : newSet.add(key);
      setSelectedPlantCells(newSet);
    }
  };

  if (!gardens) return <GridLoading />;

  return (
    <>
      <NavBar
        title="Dashboard"
        buttonOptions={['back', 'settings', 'bell']}
        username={username}
        onBack={() => { window.location.href = import.meta.env.VITE_BACKEND_URL; }}
      />
      <PlantSearchSideBar
        page="dashboard"
        onPlantClick={handlePlantClick}
        onShearClick={() => { handlePlantClick({ type: 'SHEAR' }); }}
      />
        <div className="dashboard-content" ref={containerRef}>
            <GardenBar
              selectedGardenIndex={selectedGardenIndex}
              setSelectedGardenIndex={setSelectedGardenIndex}
            />
          {gardens && (
          <GardenGrid
            selectedGardenIndex={selectedGardenIndex}
            fontSize={fontSize}
            squareSize={squareSize}
            contentSize={contentSize}
            selectedEmptyCells={selectedEmptyCells}
            selectedPlantCells={selectedPlantCells}
            cellClickHandler={cellClickHandler}
          />

          )}
          <div
            className="garden-notification-container"
            style={{
              borderTop: '2px solid black',
              alignSelf: 'end',
              height: `${contentSize}px`,
            }}
          >
          <NotificationSection
            contentSize={contentSize}
            selectedGardenIndex={selectedGardenIndex}
          />
          
        </div>
    </div>
    </>
  );
}

export default DashboardPage;
