import React from 'react';
import TextButton from './TextButton';
import './styles/btn-styles.css';
import { useState, useEffect } from 'react';

function GardenButton({ text, style, onRightClick, onLeftClick }) {
    const [fontSize, setFontSize] = useState(16);

    useEffect(() => {
        
        const adjustFontSize = () => {
            const buttonWidth = 120;
            const padding = 16;
            const context = document.createElement('canvas').getContext('2d');
            let currentFontSize = 16;
            context.font = `${currentFontSize}px Arial`;
    
            while (context.measureText(text).width > (buttonWidth - padding) && currentFontSize > 10) {
                currentFontSize -= 1;
                context.font = `${currentFontSize}px Arial`;
            }
    
            setFontSize(currentFontSize);
        };
    
        adjustFontSize();
    }, [text]);
    
    return (
        <TextButton
            text={text}
            style={{ ...style, width: '120px', fontSize: `${fontSize}px` }}
            className="garden-btn"
            onRightClick={onRightClick}
            onLeftClick={onLeftClick}
        />
    );
}

export default GardenButton;