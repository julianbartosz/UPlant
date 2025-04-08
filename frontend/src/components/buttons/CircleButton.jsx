import React from 'react';
import './styles/btn-styles.css'; 

function CircleButton({className, onClick, text=""}) {
    return (
        <button 
            className={`circle-btn ${className}`} 
            onClick={onClick} >
            {text}
        </button>
    );
    }

export default CircleButton;