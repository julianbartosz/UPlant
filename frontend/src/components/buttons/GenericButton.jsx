
import React from 'react';

const GenericButton = ({ onClick, label, style, disableMouseOver=false }) => {
    const buttonStyle = {
        color: 'white',
        padding: '10px 20px',
        border: 'none',
        borderRadius: '5px',
        cursor: 'pointer',
        fontSize: '16px',
        ...style,
    };

    const handleMouseOver = (e) => {
        if (!disableMouseOver) {
            e.target.style.transform = 'scale(1.1)';
            e.target.style.transition = 'transform 0.2s ease-in-out';
        }
    };
    
    const handleMouseOut = (e) => {
        if (!disableMouseOver) {
            e.target.style.transform = 'scale(1)';
        }
    };

    return (
        <button
            style={buttonStyle}
            onClick={onClick}
            onMouseOver={handleMouseOver}
            onMouseOut={handleMouseOut}
        >
            {label || 'Update'}
        </button>
    );
};

export default GenericButton;