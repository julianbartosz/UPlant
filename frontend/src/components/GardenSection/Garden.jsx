import React, { useRef, useEffect, useState } from 'react';
import './Garden.css';

const Garden = ({ garden, cells }) => {
    const containerRef = useRef(null);
    const [fontSize, setFontSize] = useState(40); // Default font size

    useEffect(() => {
        const updateFontSize = () => {
            if (containerRef.current) {
                const containerWidth = containerRef.current.offsetWidth;
                const containerHeight = containerRef.current.offsetHeight;
                
                // Dynamically calculate font size
                const calculatedFontSize = Math.min(containerWidth / garden.x, containerHeight / garden.y) * 0.5;
                setFontSize(calculatedFontSize);
            }
        };

        // Call initially and add a resize event listener
        updateFontSize();
        window.addEventListener('resize', updateFontSize);

        return () => window.removeEventListener('resize', updateFontSize);
    }, [garden.x, garden.y]); // Recalculate when dimensions change

    const createGrid = () => {
        return cells.map((row, i) => (
            <div key={i} className="row">
                {row.map((value, j) => (
                    <div key={`${i}-${j}`} className="square" style={{ fontSize: `${fontSize}px` }}>
                        {value || ""}
                    </div>
                ))}
            </div>
        ));
    };

    return (
        <div className="container" ref={containerRef}>
            <div className="garden" style={{ 
                display: "grid",
                gridTemplateRows: `repeat(${garden.y}, 1fr)`,
                gridTemplateColumns: `repeat(${garden.x}, 1fr)`,
            }}>
                {createGrid()}
            </div>
        </div>
    );
};

export default Garden;
