import React from 'react';
import TextButton from './TextButton';
import './styles/btn-styles.css';

function BackButton({ onClick }) {
    return (
        <TextButton
            text="← Back"
            className="back-btn"
            style={{borderRadius: '5px'}}
            onLeftClick={onClick}
            onRightClick={(e) => {
                e.preventDefault();
                onClick(e);
            }}
        />
    );
}           

export default BackButton;