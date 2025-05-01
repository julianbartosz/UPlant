import React from 'react';
import './styles/btn-styles.css';

function TextButton({
    onLeftClick = () => {},
    onRightClick = () => {},
    text = "Add Text...",
    style = {},
    className = "no-style-btn",
}) {
    return (
        <div className="btn-container">
            <button
                className={className}
                onClick={onLeftClick}
                onContextMenu={(e) => {
                    e.preventDefault();
                    onRightClick(e);
                }}
                style={style}
            >
                {text}
            </button>
        </div>
    );
}

export default TextButton;