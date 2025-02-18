import React from 'react';
import './GardenBar.css';

const GardenBar = ({gardens}) => {

    // TODO: Add functionality to switch between gardens
    // TODO: Add functionality to add new gardens
    // TODO: Add functionality to delete gardens
    
    // TODO: Add functionality to dynamically adjust width and font
    const style = {
        width: '120px',
        fontSize: "14px"
    };    

    return (
        <div className="garden-bar">
            {gardens.map((garden, index) => (
                <div className='garden-bar-item' key={index}>
                    <button style={style}>{garden.name}</button>
                </div>
            ))}
        </div>
    );
};

export default GardenBar;