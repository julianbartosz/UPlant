import React from 'react';
import { useGardens } from '../../../contexts/ProtectedRoute';
import { AddButton, DeleteButton, GardenButton } from '../../buttons';
import './styles/garden-bar.css';

const GardenBar = ({ selectedGardenIndex, setSelectedGardenIndex, dynamic=true, style={} }) => {
   
    const { gardens, handleAddGarden, handleDeleteGarden, handleRenameGarden } = useGardens();
    
    if (!gardens) return (<div>Loading ...</div>); 
    
    return (
        <div className="garden-bar" style={style}>
            {dynamic && (
                <div className='garden-bar-item' key={-1}>
                    <AddButton onAdd={() =>  {
                        handleAddGarden();
                        setSelectedGardenIndex(gardens.length);
                    }} />
                </div>
            )}
               
            {gardens.map((garden, index) => (
                <div className='garden-bar-item' key={index}>
                    {dynamic && (
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
                    )}
                    
                    <GardenButton
                        onRightClick={(e) => {
                            e.preventDefault();
                            if (dynamic) handleRenameGarden(index);
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