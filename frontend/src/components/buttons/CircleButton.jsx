import React from 'react';
import './styles/btn-styles.css'; 
import { FaArrowRight } from 'react-icons/fa';


function CircleButton({className, onClick, text="", Icon}) {
    return (
        <button 
            className={`circle-btn ${className}`} 
            style={{paddingTop: '5px'}}
            onClick={onClick} >
            {text}
            {Icon}
        </button>
    );
    }

export default CircleButton;