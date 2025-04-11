import React from 'react';
import TextButton from './TextButton';
import './styles/btn-styles.css';

function GardenButton({ text, style, onRightClick, onLeftClick}) {
    return (
        <TextButton 
            text={text}
            style={style}
            className="garden-btn"
            onRightClick={onRightClick}
            onLeftClick={onLeftClick} />
    );
}

export default GardenButton;