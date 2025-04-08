import React from 'react';
import { useGardens } from '../../../contexts/ProtectedRoute';
import { AddButton, DeleteButton, GardenButton } from '../../buttons';
import './styles/garden-bar.css';

const GardenBar = ({ selectedGardenIndex, setSelectedGardenIndex }) => {
   
    const { gardens, handleAddGarden, handleDeleteGarden, handleRenameGarden } = useGardens();

    return (
        <div className="garden-bar">
            <div className='garden-bar-item' key={-1}>
              <AddButton onAdd={() =>  {
                handleAddGarden();
                setSelectedGardenIndex(gardens.length);
              }} />
            </div>
               
            {gardens.map((garden, index) => (
                <div className='garden-bar-item' key={index}>
                     <DeleteButton 
                        onDelete={() => {
                            if (gardens.length <= 1) {
                                alert("You cannot delete the last garden.");
                                return;
                            }
                            handleDeleteGarden(index);
                            if (selectedGardenIndex === index) {
                                setSelectedGardenIndex(0);
                            } else if (selectedGardenIndex > index) {
                                setSelectedGardenIndex(selectedGardenIndex - 1);
                            }
                        }} 
                    />
                    
                    <GardenButton
                        onRightClick={(e) => {
                            e.preventDefault();
                            handleRenameGarden(index);
                        }} 
                        onLeftClick={() => {
                            setSelectedGardenIndex(index)
                        }} 
                        text={garden.name}
                        style={{ borderRadius: '4px', color: "black", backgroundColor: selectedGardenIndex === index ? 'green' : 'lightgreen' }}
                    />
                
                </div>
            ))}
        </div>
    );
};

export default GardenBar;