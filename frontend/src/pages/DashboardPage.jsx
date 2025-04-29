import { useRef, useEffect, useState } from 'react';
import { useGardens, useUser } from '../hooks';
import { GardenGrid } from '../components/ui';
import { NotificationSection, GardenBar, PlantSearchSideBar, NavBar } from '../components/layout';
import { GridLoading } from '../components/widgets';
import { UserContext } from '../context/UserProvider';
import { useContext } from 'react';
import { GardenForm } from '../components/forms';

import './styles/dashboard-page.css';
import useContentSize from '../hooks/useContentSize';

function DashboardPage() {
   
  const { gardens, dispatch, loading } = useContext(UserContext);

  const [selectedGardenIndex, setSelectedGardenIndex] = useState(0);
  const [selectedEmptyCells, setSelectedEmptyCells] = useState(new Set());
  const [selectedPlantCells, setSelectedPlantCells] = useState(new Set());
  const [toggleForm, setToggleForm] = useState(false);
  
  
  const containerRef = useRef(null);
  const contentSize = useContentSize(containerRef);
  const selectedGardenIndexRef = useRef(selectedGardenIndex);
  const selectedEmptyCellsRef = useRef(selectedEmptyCells);
  const selectedPlantCellsRef = useRef(selectedPlantCells);
  
  useEffect(() => { selectedEmptyCellsRef.current = selectedEmptyCells; }, [selectedEmptyCells]);
  useEffect(() => { selectedPlantCellsRef.current = selectedPlantCells; }, [selectedPlantCells]);

  // useEffect(() => {
  //   if (!containerRef.current) return;
  //     const { width, height } = containerRef.current.getBoundingClientRect();
  //     console.log("Width: ", width, "Height: ", height);
  //     dispatch({ type: 'UPDATE_CONTENT', payload: { width, height } });
  //  }, [selectedGardenIndex]);
  

  // useEffect(() => {
  //   selectedGardenIndexRef.current = selectedGardenIndex;
  //   setSelectedEmptyCells(new Set());
  //   setSelectedPlantCells(new Set());
    
  //   const handleResize = () => {
  //     if (containerRef.current && gardens && gardens.length > 0) {
  //       const { width, height } = containerRef.current.getBoundingClientRect();
  //       const maxDimension = Math.max(gardens[selectedGardenIndexRef.current].size_x, gardens[selectedGardenIndexRef.current].size_y);
  //       const newSquareSize = Math.min(width * 0.6, height * 0.6) / maxDimension;
  //       setFontSize(newSquareSize * 0.5);
  //       setContentSize(height - 88);
  //       setSquareSize(newSquareSize);
  //     }
  //   };
    
  //   if (gardens && gardens.length > selectedGardenIndexRef.current) {
  //     handleResize();
  //   }

  //   window.addEventListener('resize', handleResize);
  //   return () => window.removeEventListener('resize', handleResize);
  // }, [selectedGardenIndex, gardens]);

 
  if (loading) {
    return <GridLoading />;
  }
  const handlePlantClick = (item) => {
    if (item.type === 'SHEAR') {
      selectedPlantCellsRef.current.forEach(key => {
        const [row, col] = key.split('-').map(Number);
        if (row < gardens[selectedGardenIndexRef.current].size_y && col < gardens[selectedGardenIndexRef.current].size_x) mediateRemovePlantFromGarden(gardens[selectedGardenIndexRef.current].id, row, col);
      });
      return;
      
    }
    

    const currentGarden = gardens[selectedGardenIndexRef.current]
      selectedEmptyCellsRef.current.forEach(key => {
        const [row, col] = key.split('-').map(Number);
        console.log("ROW COL: ", row, col);
        if (row < currentGarden.size_y && col < currentGarden.size_x) mediateAddPlantToGarden(selectedGardenIndexRef.current, item, row, col);
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
              onAdd={() => { setToggleForm(!toggleForm); }}
            />
          {!loading && 
          <div className={ "garden-grid-container" } style={{height: `${contentSize.height-88}px`}}>
          {!toggleForm ? (
        <GardenGrid
            selectedGardenIndex={selectedGardenIndex}
            contentSize={contentSize}
            selectedEmptyCells={selectedEmptyCells}
            selectedPlantCells={selectedPlantCells}
            cellClickHandler={cellClickHandler}
          />

          ) : <GardenForm callback={() => {setToggleForm(false);}} />}
          </div>
          }
          

          <div
            className="garden-notification-container"
            style={{
              borderTop: '2px solid black',
              alignSelf: 'end',
              height: `${contentSize.height - 88}px`,
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
